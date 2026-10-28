#!/usr/bin/env python3
"""EXP-2/3: protocol-correct per-cell OOF evaluation for AP-1 variants.

For each of the 8 hide-and-recover cells, dots are re-emitted from the frozen
surface using ONLY that cell's visible catalogue for the B=2 collar (refill to
37,654), then scored with holdout.evaluate_hide_and_recover (NPZ mode, b=0).
Champion control: parent d2.8 mask scored in single-mask mode with b_visible=2
(fold-local B2 gate, no refill — budget difference disclosed in the receipt).
SGMC is scored on the final full-catalogue masks (no hide/recover involved).
"""
from __future__ import annotations

import argparse, json, os, sys, time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from apart import surface as S  # noqa: E402
from apart.emit import score_ordered_dots  # noqa: E402
from run_experiment import paired_delta  # noqa: E402


def main() -> int:
    from experiment_guard import require_current_protocol
    if not require_current_protocol():
        return 1
    print("BLOCKED: archived AP-1 OOF runner used an unmatched historical control.", file=sys.stderr)
    return 1
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variant", choices=["equal", "strain2"], default="strain2")
    ap.add_argument("--order", choices=["raw", "smooth"], default="smooth")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--data-dir", default=os.environ.get("GEMS_DATA_DIR", "/tmp/gems_data"))
    ap.add_argument("--work-dir", default="/tmp/apart_work")
    args = ap.parse_args()
    t0 = time.time()
    ddir = Path(args.data_dir); work = Path(args.work_dir)
    foot, labels = S.footprint_and_labels(ddir)
    z = np.load(work / "ranks.npz"); ranks = {k: z[k] for k in z.files}
    surf = S.combine(ranks, args.variant)
    np.save(work / f"surface_{args.tag}_{args.variant}_{args.order}.npy", surf)

    order_field = surf
    if args.order == "smooth":
        from scipy.ndimage import gaussian_filter
        order_field = gaussian_filter(surf, sigma=1.0, mode="nearest").astype(np.float32)

    from gems32 import holdout
    ctx = holdout.load_holdout_context(ddir)
    print(f"ctx ready {time.time()-t0:.0f}s; cells={[c.key for c in ctx.cells]}")

    cells: dict[str, np.ndarray] = {}
    for cell in ctx.cells:
        vis = ctx.visible_by_cell[cell.key]
        m = score_ordered_dots(surf, foot, vis, order_field=order_field, pool=450000)
        cells[cell.key] = m
        print(f"{cell.key}: OOF dots={m.sum()} ({time.time()-t0:.0f}s)")

    res_cand = holdout.evaluate_hide_and_recover(cells, ctx, b_visible_px=0.0, name=f"AP1-{args.tag}-OOF")
    import rasterio
    with rasterio.open("/tmp/gems_data/registry_focus/GEMSDOE25_best.tif") as ds:
        d28 = ds.read(1) > 0
    with rasterio.open("/tmp/gems_data/registry_focus/GEMSDOE32_best.tif") as ds:
        champ = ds.read(1) > 0
    res_champ_oof = holdout.evaluate_hide_and_recover(d28, ctx, b_visible_px=2.0, name="CTRL-champion-foldlocal-B2(no-refill)")

    final_mask = score_ordered_dots(surf, foot, labels, order_field=order_field, pool=450000)
    np.save(work / f"mask_{args.tag}.npy", final_mask)
    np.save(work / f"surface_final_{args.tag}.npy", surf)
    sg_cand = holdout.evaluate_sgmc_with_ci(final_mask, ctx, name=f"AP1-{args.tag}")
    sg_champ = holdout.evaluate_sgmc_with_ci(champ, ctx, name="CTRL-champion-B2")
    paired = paired_delta(res_cand["folds"], res_champ_oof["folds"])

    def slim(r):
        return {"pooled_dti": r["pooled_dti"], "ci95": r.get("ci95_cluster_bootstrap") or r.get("ci95"),
                "n_withheld_positives": r["n_withheld_positives"], "evaluator_version": r["evaluator_version"],
                "folds": r["folds"]}

    out = {"tag": args.tag, "variant": args.variant, "order": args.order, "mode": "per-cell-OOF visible-only collar, refill 37654",
           "evidence_class": "HOLDOUT-DTI",
           "candidate_oof": slim(res_cand),
           "control_champion_foldlocal": slim(res_champ_oof),
           "paired_vs_champion_foldlocal": paired,
           "sgmc_candidate_final": sg_cand, "sgmc_champion_final": sg_champ,
           "note_budget": "candidate refills to 37,654 per cell; champion control gates d2.8 by visible B2 without refill (emitted per fold in folds[*].emitted) — disclosed, conservative for candidate on mass, exact on placement rule.",
           "elapsed_s": round(time.time() - t0, 1)}
    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items() if not str(k).startswith("_")}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, (np.floating, np.integer, np.bool_)):
            return o.item()
        return o

    dest = ROOT / "evidence" / f"experiment_{args.tag}.json"
    dest.write_text(json.dumps(clean(out), indent=1) + "\n")
    print(f"CAND OOF {res_cand['pooled_dti']:.4f} {res_cand['ci95_cluster_bootstrap']} vs CHAMP-foldlocal {res_champ_oof['pooled_dti']:.4f} {res_champ_oof['ci95_cluster_bootstrap']}")
    print(f"paired {paired}")
    print(f"SGMC cand cal={sg_cand.get('prevalence_calibrated_dti')} raw={sg_cand.get('raw_pooled_dti')} | champ cal={sg_champ.get('prevalence_calibrated_dti')} raw={sg_champ.get('raw_pooled_dti')}")
    print(f"wrote {dest} in {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
