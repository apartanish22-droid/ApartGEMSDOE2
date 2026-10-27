#!/usr/bin/env python3
"""Run one AP-1 experiment: surface -> canary -> emission -> hide-and-recover + SGMC.

Usage: python scripts/run_experiment.py --variant equal --order raw --tag exp1
Data dir resolution: --data-dir, else $GEMS_DATA_DIR, else /tmp/gems_data.
All scores printed are HOLDOUT-DTI (see knowledge/preregistration-20261027.md).
"""
from __future__ import annotations

import argparse, json, os, sys, time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apart import surface as S  # noqa: E402
from apart.emit import score_ordered_dots, random_dots  # noqa: E402


def paired_delta(cand_cells: dict, ctrl_cells: dict, n_boot=2000, seed=7):
    keys = sorted(set(cand_cells) & set(ctrl_cells))
    c = [(cand_cells[k]["tp"], cand_cells[k]["fp"], cand_cells[k]["n_truth"]) for k in keys]
    h = [(ctrl_cells[k]["tp"], ctrl_cells[k]["fp"], ctrl_cells[k]["n_truth"]) for k in keys]

    def pooled(rows):
        tp = sum(r[0] for r in rows); fp = sum(r[1] for r in rows); n = sum(r[2] for r in rows)
        return tp / (tp + 0.2 * fp + 0.8 * (n - tp) + 1e-12)

    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(keys), len(keys))
        diffs.append(pooled([c[i] for i in pick]) - pooled([h[i] for i in pick]))
    return {"paired_delta": float(pooled(c) - pooled(h)),
            "paired_ci95": [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))],
            "n_cells": len(keys)}


def main() -> int:
    raise SystemExit('STOP: archived parallel lane failed the literal lattice novelty gate and the experiment budget was reported spent; no new run or promotion is authorized.')
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variant", choices=["equal", "strain2"], default="equal")
    ap.add_argument("--order", choices=["raw", "smooth"], default="raw",
                    help="smooth: order emission by 300m-kernel-smoothed surface (EXP-2)")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--data-dir", default=os.environ.get("GEMS_DATA_DIR", "/tmp/gems_data"))
    ap.add_argument("--work-dir", default="/tmp/apart_work")
    ap.add_argument("--with-random", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    ddir = Path(args.data_dir); work = Path(args.work_dir); work.mkdir(parents=True, exist_ok=True)
    foot, labels = S.footprint_and_labels(ddir)
    print(f"footprint={foot.sum()} labels={labels.sum()}")

    rank_cache = work / "ranks.npz"
    if rank_cache.exists():
        z = np.load(rank_cache)
        ranks = {k: z[k] for k in z.files}
        print("ranks: cache hit")
    else:
        ranks = S.build_components(str(ddir / "training_features.tif"), foot)
        np.savez_compressed(rank_cache, **ranks)
        print(f"ranks: built in {time.time()-t0:.0f}s")

    canary = {}
    for k in ["dilatation", "shear", "second_invariant", "cond_edge", "base_edge", "grav_edge", "strain"]:
        a = S.auc_rank(ranks[k], labels, foot)
        canary[k] = {"auc": a, "auc_two_sided_max": max(a, 1 - a), "leakage_flag_gt_0.90": bool(max(a, 1 - a) > 0.90)}
        print(f"canary {k}: AUC={a:.4f}")

    surf = S.combine(ranks, args.variant)
    np.save(work / f"surface_{args.tag}_{args.variant}_{args.order}.npy", surf)
    canary["AP1_surface"] = {"auc": S.auc_rank(surf, labels, foot)}
    canary["AP1_surface"]["leakage_flag_gt_0.90"] = bool(canary["AP1_surface"]["auc"] > 0.90)
    print(f"canary AP1_surface: AUC={canary['AP1_surface']['auc']:.4f}")

    # --- pre-placement surface uniqueness (sampled Spearman vs 9 champions) ---
    from scipy.stats import spearmanr
    rng = np.random.default_rng(0)
    fy, fx = np.nonzero(foot)
    sel = rng.choice(fy.size, size=min(300000, fy.size), replace=False)
    svals = surf[fy[sel], fx[sel]]
    surf_rho = {}
    reg = Path("/tmp/gems_data/registry_focus")
    champ_masks = {}
    for p in sorted(reg.glob("GEMSDOE*_best.tif")):
        import rasterio
        with rasterio.open(p) as ds:
            m = ds.read(1) > 0
        champ_masks[p.stem] = m
        rho = float(spearmanr(svals, m[fy[sel], fx[sel]]).statistic)
        surf_rho[p.stem] = rho
        print(f"surface Spearman vs {p.stem}: {rho:+.4f}")
    assert max(abs(v) for v in surf_rho.values()) <= 0.90, "SURFACE DRIFT STOP"

    order_field = surf
    if args.order == "smooth":
        from scipy.ndimage import gaussian_filter
        order_field = gaussian_filter(surf, sigma=1.0, mode="nearest").astype(np.float32)

    mask = score_ordered_dots(surf, foot, labels, order_field=order_field)
    print(f"dots={mask.sum()} oncat={(mask & labels).sum()}")
    np.save(work / f"mask_{args.tag}.npy", mask)

    # --- holdout evaluation (canonical vendored evaluator) ---
    from gems32 import holdout
    ctx = holdout.load_holdout_context(ddir)
    print(f"holdout ctx: {len(ctx.cells)} cells, withheld/cell={[c.n_truth for c in ctx.cells]}, sgmc={ctx.sgmc_n_truth}")

    def ev(m, name):
        return holdout.evaluate_visible_gated_holdout(m, ctx, b_gate_px=2.0, name=name)

    res_cand = ev(mask, f"AP1-{args.tag}")
    res_champ = ev(champ_masks["GEMSDOE32_best"], "CTRL-champion-B2")
    res_d28 = ev(champ_masks["GEMSDOE25_best"], "CTRL-d2.8")
    paired = paired_delta(res_cand["cells"], res_champ["cells"])
    out = {
        "tag": args.tag, "variant": args.variant, "order": args.order,
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": res_cand["evaluator_version"],
        "canary_auc": canary,
        "surface_spearman_vs_registry_sample300k": surf_rho,
        "candidate": {"pooled_dti": res_cand["pooled_dti"], "ci95": res_cand["ci95"],
                      "n_withheld_positives": res_cand["n_withheld_positives"],
                      "sgmc_off_catalogue": res_cand["sgmc_off_catalogue"],
                      "cells": res_cand["cells"]},
        "control_champion_B2": {"pooled_dti": res_champ["pooled_dti"], "ci95": res_champ["ci95"],
                                "n_withheld_positives": res_champ["n_withheld_positives"],
                                "sgmc_off_catalogue": res_champ["sgmc_off_catalogue"]},
        "control_d2.8": {"pooled_dti": res_d28["pooled_dti"], "ci95": res_d28["ci95"],
                         "sgmc_off_catalogue": res_d28["sgmc_off_catalogue"]},
        "paired_vs_champion": paired,
        "elapsed_s": round(time.time() - t0, 1),
    }
    if args.with_random:
        rmask = random_dots(foot, labels)
        np.save(work / "mask_random.npy", rmask)
        res_r = ev(rmask, "CTRL-random-matched")
        out["control_random_matched"] = {"pooled_dti": res_r["pooled_dti"], "ci95": res_r["ci95"],
                                         "sgmc_off_catalogue": res_r["sgmc_off_catalogue"]}
    dest = ROOT / "evidence" / f"experiment_{args.tag}.json"
    dest.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ["candidate", "control_champion_B2", "control_d2.8", "paired_vs_champion"]}, indent=1)[:2500])
    print(f"wrote {dest} in {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
