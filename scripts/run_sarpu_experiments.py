#!/usr/bin/env python3
"""Execute the 3 pre-registered H-SARPU experiments (knowledge/preregistration_sarpu_20261028.md).

Pre-registered 3-experiment factorial at K = 37,654 dots (min_sep = 2.85 px, B = 2.0 px):
  EXP-1 (SARPU-PureBlind-38k)         : 100% pure-physical SAR-PU + Blind Hydrothermal Conduit
                                        (65/60 channels, zero visible-catalogue geometry features).
  EXP-2 (SARPU-LEFM-Uncapped-38k)     : Uncapped 5-fold-isomorphic Coupled LEFM (Williams Mode-I/II
                                        + Crider-Pollard relay) + SAR-PU (67/62 channels).
  EXP-3 (SARPU-TwoRegime-Balanced-38k): Two-Stage Collar-Capped Residual 300 m Submodular Allocation
                                        (42% = 15,815 dots Coupled LEFM+SAR-PU in 2 < d_vis <= 15 px;
                                         58% = 21,839 dots Pure-Physical SAR-PU in d_vis > 15 px).

Reuses shared template evaluators (`gems32.holdout`, `gems32.registry_audit`) without modification.
"""
from __future__ import annotations

import gc
import json
import resource
import sys
import time
from pathlib import Path

import numpy as np
from numpy.lib.format import open_memmap
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems32 import holdout, paths, registry_audit, sarpu, udsr  # noqa: E402
from run_udsr_experiments import paired_delta_from_boots, strip_private  # noqa: E402

BUDGET_FULL = 37654
MIN_SEP_PX = 2.85
B_PX = 2.0
D_COLLAR_PX = 15.0
COLLAR_FRAC = 0.42
SEED = 20261028
CURRENT_BEST_HR = 0.113696  # H-UDSR EXP-2 repo holdout best (failed sparse overlap at 80.62%)


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def spatial_profile(mask: np.ndarray, d_cat: np.ndarray, lid_valid: np.ndarray) -> dict:
    d = d_cat[mask]
    lv = lid_valid[mask]
    return {
        "n_dots": int(mask.sum()),
        "frac_d_le_2px": round(float((d <= 2.0).mean()), 5) if d.size else 0.0,
        "frac_d_2_to_15px": round(float(((d > 2.0) & (d <= 15.0)).mean()), 5) if d.size else 0.0,
        "frac_d_gt_15px": round(float((d > 15.0).mean()), 5) if d.size else 0.0,
        "frac_in_lidar_gap": round(float((~lv).mean()), 5) if lv.size else 0.0,
    }


def main() -> int:
    t0 = time.time()
    ddir = paths.data_dir()
    wdir = paths.work_dir()
    tpl_tif = ddir / "sample_submission.tif"

    info = sarpu.build_sarpu_stack(ddir, wdir, force=False, log=log)
    foot = info["foot"]
    lid_valid = info["lidar_valid"]
    flat_playa = info["flat_deep_playa"]

    ctx = holdout.load_holdout_context(ddir)
    base_mm = open_memmap(wdir / "feature_stack_35.npy", mode="r")
    udsr_mm = open_memmap(wdir / "udsr_stack_18.npy", mode="r")
    sarpu_mm = open_memmap(wdir / "sarpu_stack_12.npy", mode="r")
    blind_full = np.array(sarpu_mm[:, :, 11], dtype=np.float32, copy=True)
    udsr._drop_mm_cache(sarpu_mm)

    d_cat_full = distance_transform_edt(~ctx.labels).astype(np.float32)
    elig_full_count = int((foot & (~flat_playa) & (d_cat_full > B_PX)).sum())
    collars = {
        fold: binary_dilation(ctx.quad == fold, structure=np.ones((3, 3), bool), iterations=holdout.COLLAR_PX) & foot
        for fold in holdout.FOLDS
    }

    # 1. Protocol Rule 4: Single-feature Leakage Canary across all 67 channels
    canary_path = ROOT / "evidence/sarpu_canary_67_20261028.json"
    if canary_path.exists():
        canary = json.loads(canary_path.read_text())
        log(f"[Canary] Loaded verified 67-channel canary: passed={canary['passed']} worst={canary['worst_channel']} ({canary['max_oriented_auc']})")
    else:
        canary = sarpu.run_leakage_canary_67(base_mm, udsr_mm, sarpu_mm, ctx)
        canary_path.write_text(json.dumps(canary, indent=2) + "\n")
        log(f"[Canary] Computed 67-channel canary: passed={canary['passed']} worst={canary['worst_channel']} ({canary['max_oriented_auc']})")
    if not canary["passed"]:
        log("[STOP] Protocol Rule 4 leakage canary failed (> 0.90); aborting.")
        return 2

    # 2. Reference baselines (controls only; zero experiment budget consumed)
    eman = json.loads((ROOT / "registry/extended_registry_manifest.json").read_text())
    b2_entry = next(e for e in eman["rasters"] if e.get("sha256", "").startswith("c55bafc4"))
    b2_mask = holdout.read_binary(ROOT / b2_entry["local"])
    d28_mask = holdout.read_binary(ddir / "scored/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif")
    rep_b2_static = holdout.evaluate_hide_and_recover(b2_mask, ctx, b_visible_px=0.0, name="GEMSDOE32_B2_static")
    rep_b2_honest = holdout.evaluate_hide_and_recover(d28_mask, ctx, b_visible_px=2.0, name="D28_B2_fold_honest")
    rep_b2_det600 = holdout.evaluate_hide_and_recover(d28_mask, ctx, b_visible_px=6.0, name="D28_B2_detached_600m")
    sgmc_b2 = holdout.evaluate_sgmc_with_ci(b2_mask, ctx, name="GEMSDOE32_B2")
    log(
        f"[Baselines] B2_static={rep_b2_static['pooled_dti']:.6f} | D28_B2_honest={rep_b2_honest['pooled_dti']:.6f} "
        f"| D28_det600={rep_b2_det600['pooled_dti']:.6f} | B2_SGMC_cal={sgmc_b2['sgmc_prevalence_calibrated_dti']:.6f}"
    )

    # 3. Spatially-blocked 8-cell Hide-and-Recover evaluation across EXP-1, EXP-2, EXP-3
    ckpt_dir = wdir / "sarpu_ckpt"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    cells = {"EXP-1": {}, "EXP-2": {}, "EXP-3": {}}
    for idx_c, cell in enumerate(ctx.cells):
        c_file = ckpt_dir / f"cell_{cell.key}.npz"
        if c_file.exists():
            z = np.load(c_file)
            cells["EXP-1"][cell.key] = z["d1"].astype(bool)
            cells["EXP-2"][cell.key] = z["d2"].astype(bool)
            cells["EXP-3"][cell.key] = z["d3"].astype(bool)
            log(f"  [Holdout {idx_c + 1}/8 {cell.key}] loaded from checkpoint")
            continue
        tc = time.time()
        sl = cell.bbox
        elig_cell = cell.active_sub & (cell.d_visible_sub > B_PX)
        elig_np_count = int((elig_cell & (~flat_playa[sl])).sum())
        b_cell = int(round(BUDGET_FULL * elig_np_count / max(elig_full_count, 1)))
        train_dom = foot & (~collars[cell.fold])

        models = sarpu.fit_sarpu_dual_systems(
            train_dom, cell.visible_full, foot, lid_valid, base_mm, udsr_mm, sarpu_mm, seed=SEED + idx_c * 19
        )
        lefm_cell = sarpu.compute_lefm_continuation(cell.visible_full, foot)[sl]
        p_pure, p_coup = sarpu.predict_sarpu_dual_bbox(
            sl, elig_cell, lid_valid, base_mm, udsr_mm, sarpu_mm, lefm_cell, models
        )
        del models, lefm_cell
        gc.collect()

        u_pure, u_coup, _ = sarpu.build_sarpu_surfaces(
            p_pure, p_coup, blind_full[sl], cell.active_sub, cell.d_visible_sub, flat_playa[sl], d_collar=D_COLLAR_PX
        )
        d1, _ = sarpu.emit_two_regime_dots(
            u_pure, u_pure, cell.active_sub, cell.d_visible_sub, flat_playa[sl],
            k_dots=b_cell, collar_frac=1.0, d_collar=1e9, min_fault_dist_px=B_PX, min_sep_px=MIN_SEP_PX,
        )
        d2, _ = sarpu.emit_two_regime_dots(
            u_coup, u_coup, cell.active_sub, cell.d_visible_sub, flat_playa[sl],
            k_dots=b_cell, collar_frac=1.0, d_collar=1e9, min_fault_dist_px=B_PX, min_sep_px=MIN_SEP_PX,
        )
        d3, st3 = sarpu.emit_two_regime_dots(
            u_coup, u_pure, cell.active_sub, cell.d_visible_sub, flat_playa[sl],
            k_dots=b_cell, collar_frac=COLLAR_FRAC, d_collar=D_COLLAR_PX, min_fault_dist_px=B_PX, min_sep_px=MIN_SEP_PX,
        )
        m1, m2, m3 = (d1 > 0.5), (d2 > 0.5), (d3 > 0.5)
        np.savez_compressed(c_file, d1=m1.astype(np.uint8), d2=m2.astype(np.uint8), d3=m3.astype(np.uint8))
        cells["EXP-1"][cell.key] = m1
        cells["EXP-2"][cell.key] = m2
        cells["EXP-3"][cell.key] = m3
        del p_pure, p_coup, u_pure, u_coup, d1, d2, d3
        gc.collect()
        log(
            f"  [Holdout {idx_c + 1}/8 {cell.key}] k={b_cell} (EXP3 col={st3['n_collar']}/far={st3['n_far']}) "
            f"in {time.time() - tc:.1f}s | RSS={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.0f} MiB"
        )

    exp_meta = (
        ("EXP-1", "SARPU-PureBlind-38k"),
        ("EXP-2", "SARPU-LEFM-Uncapped-38k"),
        ("EXP-3", "SARPU-TwoRegime-Balanced-38k"),
    )
    hr = {}
    hr_det600 = {}
    for eid, title in exp_meta:
        hr[eid] = holdout.evaluate_hide_and_recover(cells[eid], ctx, b_visible_px=B_PX, name=f"{eid}_{title}")
        hr_det600[eid] = holdout.evaluate_hide_and_recover(
            cells[eid], ctx, b_visible_px=6.0, name=f"{eid}_{title}_det600m"
        )
        log(
            f"[HR] {eid} ({title}) HOLDOUT-DTI={hr[eid]['pooled_dti']:.6f} "
            f"CI={[round(x, 5) for x in hr[eid]['ci95_cluster_bootstrap']]} | "
            f"DETACHED-600m={hr_det600[eid]['pooled_dti']:.6f}"
        )
    del cells
    gc.collect()

    # 4. Full-Map 4-Quadrant Collared OOF Posteriors & Candidate Emission
    log("[Full-Map OOF] Stitching 4-quadrant collared SAR-PU + LEFM posteriors...")
    p_pure_full = np.zeros(foot.shape, dtype=np.float32)
    p_coup_full = np.zeros(foot.shape, dtype=np.float32)
    lefm_all_cat = sarpu.compute_lefm_continuation(ctx.labels, foot)

    for fold in holdout.FOLDS:
        q_mask = (ctx.quad == fold) & foot
        sl_q = ctx.quad_bboxes[fold]
        f_ckpt = ckpt_dir / f"oof_fold_{fold}.npz"
        if f_ckpt.exists():
            zf = np.load(f_ckpt)
            p_pure_full[sl_q] = np.where(q_mask[sl_q], zf["pp"], p_pure_full[sl_q])
            p_coup_full[sl_q] = np.where(q_mask[sl_q], zf["pc"], p_coup_full[sl_q])
            log(f"  [Full-Map Fold {fold + 1}/4] loaded from checkpoint")
            continue
        tf = time.time()
        train_dom = foot & (~collars[fold])
        vis_train_only = ctx.labels & train_dom
        models_q = sarpu.fit_sarpu_dual_systems(
            train_dom, vis_train_only, foot, lid_valid, base_mm, udsr_mm, sarpu_mm, seed=SEED + 600 + fold * 37
        )
        q_sub = q_mask[sl_q] & (d_cat_full[sl_q] > B_PX)
        pp_q, pc_q = sarpu.predict_sarpu_dual_bbox(
            sl_q, q_sub, lid_valid, base_mm, udsr_mm, sarpu_mm, lefm_all_cat[sl_q], models_q
        )
        np.savez_compressed(f_ckpt, pp=pp_q, pc=pc_q)
        p_pure_full[sl_q] = np.where(q_mask[sl_q], pp_q, p_pure_full[sl_q])
        p_coup_full[sl_q] = np.where(q_mask[sl_q], pc_q, p_coup_full[sl_q])
        del models_q, pp_q, pc_q
        gc.collect()
        log(f"  [Full-Map Fold {fold + 1}/4] {time.time() - tf:.1f}s")
    del lefm_all_cat

    u_pure_map, u_coup_map, u_two_map = sarpu.build_sarpu_surfaces(
        p_pure_full, p_coup_full, blind_full, foot, d_cat_full, flat_playa, d_collar=D_COLLAR_PX
    )
    del p_pure_full, p_coup_full, blind_full
    gc.collect()

    d1_map, st1_map = sarpu.emit_two_regime_dots(
        u_pure_map, u_pure_map, foot, d_cat_full, flat_playa,
        k_dots=BUDGET_FULL, collar_frac=1.0, d_collar=1e9, min_fault_dist_px=B_PX, min_sep_px=MIN_SEP_PX,
    )
    d2_map, st2_map = sarpu.emit_two_regime_dots(
        u_coup_map, u_coup_map, foot, d_cat_full, flat_playa,
        k_dots=BUDGET_FULL, collar_frac=1.0, d_collar=1e9, min_fault_dist_px=B_PX, min_sep_px=MIN_SEP_PX,
    )
    d3_map, st3_map = sarpu.emit_two_regime_dots(
        u_coup_map, u_pure_map, foot, d_cat_full, flat_playa,
        k_dots=BUDGET_FULL, collar_frac=COLLAR_FRAC, d_collar=D_COLLAR_PX, min_fault_dist_px=B_PX, min_sep_px=MIN_SEP_PX,
    )

    surfaces = {"EXP-1": u_pure_map, "EXP-2": u_coup_map, "EXP-3": u_two_map}
    masks = {"EXP-1": d1_map > 0.5, "EXP-2": d2_map > 0.5, "EXP-3": d3_map > 0.5}
    emit_stats = {"EXP-1": st1_map, "EXP-2": st2_map, "EXP-3": st3_map}
    for eid in ("EXP-1", "EXP-2", "EXP-3"):
        log(f"[Full-Map {eid}] stats={emit_stats[eid]} profile={spatial_profile(masks[eid], d_cat_full, lid_valid)}")

    np.savez(
        wdir / "sarpu_exp_checkpoint.npz",
        **{f"surf_{k}": surfaces[k] for k in surfaces},
        **{f"mask_{k}": masks[k].astype(np.uint8) for k in masks},
    )

    # 5. SGMC-CAL-v3.0 + 560-Raster Extended Registry Audit + Local Candidate Audit
    local_tifs = sorted((ROOT / "docs/downloads").glob("*.tif"))
    local_overlap: dict[str, dict] = {}
    for lt in local_tifs:
        lm = holdout.read_binary(lt) & foot
        if not lm.any():
            continue
        dm = distance_transform_edt(~lm)
        local_overlap[lt.name] = {
            "dots": int(lm.sum()),
            **{eid: round(float((dm[masks[eid]] <= 3.0).mean()), 6) for eid in masks},
        }
    log(f"[Local ApartGEMSDOE2 overlaps] {json.dumps(local_overlap)}")

    entries = []
    for eid, title in exp_meta:
        ta = time.time()
        sg = holdout.evaluate_sgmc_with_ci(masks[eid], ctx, name=f"{eid}_{title}")
        aud_s = registry_audit.audit_surface(surfaces[eid], foot, eman, root=ROOT, template_tif=tpl_tif)
        aud_d = registry_audit.audit_final_dots(
            surfaces[eid], masks[eid], foot, eman, root=ROOT, template_tif=tpl_tif, space_filling_coverage=0.70
        )
        sparse = [
            r for r in aud_d["comparisons"]
            if r.get("within_3px_fraction") is not None and not r.get("space_filling")
        ]
        worst_sparse = max(sparse, key=lambda r: float(r["within_3px_fraction"])) if sparse else None
        worst_local = max((v[eid] for v in local_overlap.values()), default=0.0)
        worst_local_name = max(local_overlap.keys(), key=lambda k: local_overlap[k][eid]) if local_overlap else None

        paired_b2h = paired_delta_from_boots(
            hr[eid]["pooled_dti"], hr[eid]["_boots"], rep_b2_honest["pooled_dti"], rep_b2_honest["_boots"]
        )
        paired_b2s = paired_delta_from_boots(
            hr[eid]["pooled_dti"], hr[eid]["_boots"], rep_b2_static["pooled_dti"], rep_b2_static["_boots"]
        )
        paired_exp1 = paired_delta_from_boots(
            hr[eid]["pooled_dti"], hr[eid]["_boots"], hr["EXP-1"]["pooled_dti"], hr["EXP-1"]["_boots"]
        )

        g2_point = bool(hr[eid]["pooled_dti"] > CURRENT_BEST_HR)
        g2_ci = bool(paired_b2h["ci95_strictly_positive"])
        g3_surf = bool(aud_s["passed"])
        g3_sparse = bool(
            (worst_sparse is None or float(worst_sparse["within_3px_fraction"]) <= 0.70)
            and worst_local <= 0.70
        )
        g3_literal = bool(aud_d["literal_rule_passed"] and worst_local <= 0.70)

        entry = {
            "experiment_id": eid,
            "name": title,
            "holdout_hide_and_recover": strip_private(hr[eid]),
            "holdout_detached_600m": strip_private(hr_det600[eid]),
            "paired_vs_b2_fold_honest": paired_b2h,
            "paired_vs_b2_static": paired_b2s,
            "paired_vs_exp1_pureblind": paired_exp1,
            "sgmc_diagnostic": strip_private(sg),
            "emit_stats": emit_stats[eid],
            "spatial_profile": spatial_profile(masks[eid], d_cat_full, lid_valid),
            "surface_audit": {
                "passed": g3_surf,
                "audit_complete": aud_s["audit_complete"],
                "registry_rasters": aud_s["registry_rasters"],
                "worst_abs_spearman": round(float(aud_s["worst_abs_spearman"]), 6),
                "worst_raster": aud_s["worst_raster"],
            },
            "dots_audit": {
                "passed_space_filling_calibrated": g3_sparse,
                "literal_rule_passed": g3_literal,
                "audit_complete": aud_d["audit_complete"],
                "registry_rasters": aud_d["registry_rasters"],
                "candidate_dots": aud_d["candidate_dots"],
                "worst_within_3px_fraction_literal": round(float(aud_d["worst_within_3px_fraction"]), 6),
                "worst_literal_raster": aud_d["worst_overlap_raster"],
                "worst_sparse_within_3px": round(float(worst_sparse["within_3px_fraction"]), 6) if worst_sparse else None,
                "worst_sparse_raster": f"{worst_sparse['repo']}:{worst_sparse['path']}" if worst_sparse else None,
                "worst_local_within_3px": round(float(worst_local), 6),
                "worst_local_raster": worst_local_name,
            },
            "gates": {
                "G1_canary": bool(canary["passed"]),
                "G2_beats_repo_best_0113696": g2_point,
                "G2_paired_ci_vs_d28_b2_positive": g2_ci,
                "G3_surface_spearman_le_090": g3_surf,
                "G3_sparse_3px_le_070": g3_sparse,
                "G3_literal_3px_le_070": g3_literal,
                "promotable_calibrated": bool(canary["passed"] and g2_point and g2_ci and g3_surf and g3_sparse),
                "promotable_literal_strict": bool(canary["passed"] and g2_point and g2_ci and g3_surf and g3_literal),
            },
        }
        entries.append(entry)
        log(
            f"[{eid} {title}] {time.time() - ta:.1f}s | HR={hr[eid]['pooled_dti']:.6f} "
            f"(d_vs_D28={paired_b2h['delta_dti']:+.6f}, CI+={g2_ci}) | DET600={hr_det600[eid]['pooled_dti']:.6f} | "
            f"SGMC_cal={sg['sgmc_prevalence_calibrated_dti']:.6f} | max|rho|={entry['surface_audit']['worst_abs_spearman']} | "
            f"worst_sparse3px={entry['dots_audit']['worst_sparse_within_3px']} ({entry['dots_audit']['worst_sparse_raster']}) | "
            f"worst_local3px={entry['dots_audit']['worst_local_within_3px']} | literal={g3_literal}"
        )

    # Select candidate: highest holdout among calibrated-unique passing candidates, else highest holdout overall
    passing_cal = [e for e in entries if e["gates"]["promotable_calibrated"]]
    selected = max(passing_cal or entries, key=lambda e: e["holdout_hide_and_recover"]["pooled_dti"])

    summary = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.time() - t0, 2),
        "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1),
        "experiment_budget_used": 3,
        "experiment_budget_max": 3,
        "lane": "H-SARPU (knowledge/preregistration_sarpu_20261028.md)",
        "canary_67": {
            "passed": canary["passed"],
            "n_features_tested": canary["n_features_tested"],
            "max_oriented_auc": canary["max_oriented_auc"],
            "worst_channel": canary["worst_channel"],
        },
        "baselines": {
            "GEMSDOE32_B2_static_holdout": strip_private(rep_b2_static),
            "D28_B2_fold_honest_holdout": strip_private(rep_b2_honest),
            "D28_B2_detached_600m_holdout": strip_private(rep_b2_det600),
            "GEMSDOE32_B2_sgmc": strip_private(sgmc_b2),
            "archived_repo_best_hr_hudsr_exp2": CURRENT_BEST_HR,
        },
        "experiments": entries,
        "local_apartgemsdoe2_overlap_within3px": local_overlap,
        "selected_experiment": selected["experiment_id"],
    }
    out_path = ROOT / "evidence/sarpu_three_experiments_20261028.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n")
    log(f"[DONE] selected={selected['experiment_id']} in {summary['elapsed_seconds']}s -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
