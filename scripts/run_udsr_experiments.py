#!/usr/bin/env python3
"""Execute the 3 pre-registered H-UDSR experiments (EXP-1, EXP-2, EXP-3) under strict budget & gates.

Reuses canonical ``gems32.holdout``, ``gems32.emitter``, and ``gems32.registry_audit`` modules:
  - EXP-1 (UDSR-PurePhysics): 100% label-free & 1m-LiDAR-free updip multi-physics crest S_phys.
  - EXP-2 (UDSR-DualCover-OOF): Pure-physical Dual-Cover OOF (53-ch M_Full + 50-ch M_Gap) Bayes-fused
    with exact bit-partition stepover relay & fault-tip cones, single-stage 1-px crest submodular emit.
  - EXP-3 (UDSR-Stratified-TwoRegime): Anti-collar-crowding two-stage residual submodular emit
    (50% Bayes-fused continuation collar 2 < d <= 15 px; 50% pure-physical updip far-field d > 15 px).
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

from gems32 import emitter, holdout, paths, registry_audit, udsr  # noqa: E402

BUDGET_FULL = 37654
MIN_SEP_PX = 2.9
B_PX = 2.0
SEED = 20261027


def strip_private(d: dict) -> dict:
    return {k: v for k, v in d.items() if not k.startswith("_")}


def paired_delta_from_boots(pt_cand: float, boots_cand: np.ndarray, pt_ref: float, boots_ref: np.ndarray) -> dict:
    diff = np.asarray(boots_cand, dtype=np.float64) - np.asarray(boots_ref, dtype=np.float64)
    lo, hi = np.percentile(diff, [2.5, 97.5])
    return {
        "delta_dti": round(float(pt_cand - pt_ref), 6),
        "ci95_paired_cluster_bootstrap": [round(float(lo), 6), round(float(hi), 6)],
        "win_fraction_boot": round(float((diff > 0.0).mean()), 4),
        "ci95_strictly_positive": bool(lo > 0.0),
    }


def emit_axial_crest_budget(
    surface: np.ndarray,
    domain: np.ndarray,
    budget: int,
    min_sep_px: float = MIN_SEP_PX,
    initial_mask: np.ndarray | None = None,
    support_mult: float = 3.6,
) -> np.ndarray:
    """Confine belief support to 4-azimuth 1-px axial ridge crests with power-law probability mass."""
    if budget <= 0 or not domain.any():
        return np.zeros(surface.shape, dtype=bool)
    crest = udsr.is_crest_4az(surface, domain) & domain
    cand_mask = crest if int(crest.sum()) >= budget * 2 else domain
    vals = np.nan_to_num(surface[cand_mask], nan=0.0)
    k = min(vals.size, max(int(round(budget * support_mult)), budget + 500))
    thr = float(vals.min()) if k >= vals.size else float(np.partition(vals, -k)[-k])
    vmax = max(float(vals.max()), 1e-6)
    norm_s = np.clip(surface / vmax, 0.0, 1.0)
    field = np.where(cand_mask & (surface >= thr), np.maximum(norm_s ** 1.5, 1e-3), 0.0).astype(np.float32)
    mask, _ = emitter.emit(
        field,
        budget=budget,
        prior_dti=0.001,
        min_sep_px=min_sep_px,
        initial_mask=initial_mask,
    )
    return mask


def emit_two_stage_stratified(
    s_near: np.ndarray,
    s_far: np.ndarray,
    foot_elig: np.ndarray,
    d_vis: np.ndarray,
    budget_total: int,
    min_sep_px: float = MIN_SEP_PX,
    near_frac: float = 0.50,
) -> tuple[np.ndarray, dict]:
    """Two-stage residual submodular placement using ``emitter.emit(..., initial_mask=mask_a)``."""
    b_near = int(round(budget_total * near_frac))
    b_far = int(budget_total - b_near)

    dom_near = foot_elig & (d_vis > B_PX) & (d_vis <= 15.0)
    mask_a = emit_axial_crest_budget(s_near, dom_near, budget=b_near, min_sep_px=min_sep_px)

    dom_far = foot_elig & (d_vis > 15.0)
    mask_b = emit_axial_crest_budget(s_far, dom_far, budget=b_far, min_sep_px=min_sep_px, initial_mask=mask_a)
    mask = mask_a | mask_b
    return mask, {
        "n_near_emitted": int(mask_a.sum()),
        "n_far_emitted": int(mask_b.sum()),
        "n_total_emitted": int(mask.sum()),
    }


def fuse_bayes_near(p_phys: np.ndarray, s_phys: np.ndarray, vis_cont_sub: np.ndarray) -> np.ndarray:
    """Orthogonal Bayes fusion of pure-physical Dual-Cover posterior with tip/relay continuation."""
    base_p = 0.86 * np.power(np.clip(p_phys, 0.0, 1.0), 1.3) + 0.14 * np.power(np.clip(s_phys, 0.0, 1.0), 2.5)
    prior_mult = 1.0 + 3.0 * vis_cont_sub[:, :, 1] + 2.2 * vis_cont_sub[:, :, 0]
    return (base_p * prior_mult).astype(np.float32)


def fuse_pure_far(p_phys: np.ndarray, s_phys: np.ndarray) -> np.ndarray:
    """Pure-physical far-field surface (zero catalogue features) combining Dual-Cover ML + S_phys."""
    return (0.78 * np.power(np.clip(p_phys, 0.0, 1.0), 1.35) + 0.22 * np.power(np.clip(s_phys, 0.0, 1.0), 2.5)).astype(
        np.float32
    )


def spatial_profile(mask: np.ndarray, d_cat: np.ndarray, lid_valid: np.ndarray, flat_playa: np.ndarray) -> dict:
    d = d_cat[mask]
    return {
        "n_dots": int(mask.sum()),
        "frac_d_le_2px": round(float((d <= 2.0).mean()), 5),
        "frac_d_2_to_15px": round(float(((d > 2.0) & (d <= 15.0)).mean()), 5),
        "frac_d_gt_15px": round(float((d > 15.0).mean()), 5),
        "frac_in_lidar_gap": round(float((~lid_valid[mask]).mean()), 5),
        "frac_in_flat_deep_playa": round(float(flat_playa[mask].mean()), 5),
    }


def summarize_dots_audit(aud: dict) -> dict:
    comps = [r for r in aud["comparisons"] if r.get("within_3px_fraction") is not None]
    sparse = [r for r in comps if not r.get("space_filling")]
    sparse_sorted = sorted(sparse, key=lambda r: -float(r["within_3px_fraction"]))
    worst_sparse = float(sparse_sorted[0]["within_3px_fraction"]) if sparse_sorted else 0.0
    worst_sparse_name = (
        f"{sparse_sorted[0]['repo']}:{sparse_sorted[0]['path']}" if sparse_sorted else None
    )
    return {
        "passed": aud["passed"],
        "registry_rasters": aud["registry_rasters"],
        "n_space_filling_rasters": sum(bool(r.get("space_filling")) for r in comps),
        "worst_sparse_within_3px": round(worst_sparse, 6),
        "worst_sparse_raster": worst_sparse_name,
        "worst_all_including_lattice_within_3px": round(float(aud["worst_within_3px_fraction"]), 6),
        "worst_abs_spearman": round(float(aud["worst_abs_spearman"]), 6),
        "top5_sparse": [
            {
                "repo": r["repo"],
                "path": r["path"],
                "dots": r["dots"],
                "within_3px_fraction": round(float(r["within_3px_fraction"]), 5),
                "spearman": round(float(r["spearman"]), 5) if r.get("spearman") is not None else None,
            }
            for r in sparse_sorted[:5]
        ],
    }


def summarize_surface_audit(aud: dict) -> dict:
    comps = [r for r in aud["comparisons"] if r.get("spearman") is not None]
    s_sorted = sorted(comps, key=lambda r: -abs(float(r["spearman"])))
    return {
        "passed": aud["passed"],
        "registry_rasters": aud["registry_rasters"],
        "worst_abs_spearman": round(float(aud["worst_abs_spearman"]), 6),
        "worst_raster": aud["worst_raster"],
        "top5": [
            {
                "repo": r["repo"],
                "path": r["path"],
                "spearman": round(float(r["spearman"]), 5),
            }
            for r in s_sorted[:5]
        ],
    }


def main() -> int:
    from experiment_guard import require_current_protocol
    if not require_current_protocol():
        return 1
    t0 = time.time()
    ddir = paths.data_dir()
    wdir = paths.work_dir()
    tpl_tif = ddir / "sample_submission.tif"
    info = udsr.build_udsr_stack(ddir, wdir, force=False)
    foot = info["foot"]
    lid_valid = info["lidar_valid"]
    flat_playa = info["flat_deep_playa"]
    foot_noplaya = foot & ~flat_playa

    ctx = holdout.load_holdout_context(ddir)
    base_mm = open_memmap(wdir / "feature_stack_35.npy", mode="r")
    udsr_mm = open_memmap(wdir / "udsr_stack_18.npy", mode="r")
    s_phys_full = np.array(udsr_mm[:, :, 14], dtype=np.float32, copy=True)

    d_cat_full = distance_transform_edt(~ctx.labels).astype(np.float32)
    elig_full_count = int((foot & (d_cat_full > B_PX)).sum())

    collars = {
        fold: binary_dilation(ctx.quad == fold, structure=np.ones((3, 3), bool), iterations=holdout.COLLAR_PX) & foot
        for fold in holdout.FOLDS
    }

    fman = json.loads((ROOT / "registry/focus_registry_manifest.json").read_text())
    eman = json.loads((ROOT / "registry/extended_registry_manifest.json").read_text())
    b2_rel = next(e["local"] for e in fman["rasters"] if e.get("sha256", "").startswith("c55bafc4"))
    b2_mask = holdout.read_binary(ROOT / b2_rel)
    d28_mask = holdout.read_binary(ddir / "scored/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif")
    h19_mask = holdout.read_binary(
        ddir / "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif"
    )

    rep_b2_static = holdout.evaluate_hide_and_recover(b2_mask, ctx, b_visible_px=0.0, name="GEMSDOE32_B2_static")
    rep_b2_honest = holdout.evaluate_hide_and_recover(d28_mask, ctx, b_visible_px=2.0, name="D28_B2_fold_honest")
    rep_h19_honest = holdout.evaluate_hide_and_recover(h19_mask, ctx, b_visible_px=2.0, name="H19_5_fold_honest")
    sgmc_b2 = holdout.evaluate_sgmc_with_ci(b2_mask, ctx, name="GEMSDOE32_B2")
    print(
        f"[Baselines] Static B2={rep_b2_static['pooled_dti']:.6f} | "
        f"Fold-honest B2={rep_b2_honest['pooled_dti']:.6f} | H19-5={rep_h19_honest['pooled_dti']:.6f} | "
        f"B2 SGMC_cal={sgmc_b2['sgmc_prevalence_calibrated_dti']:.6f}"
    )

    cells_exp1: dict[str, np.ndarray] = {}
    cells_exp2: dict[str, np.ndarray] = {}
    cells_exp3: dict[str, np.ndarray] = {}

    for idx_c, cell in enumerate(ctx.cells):
        tc = time.time()
        sl = cell.bbox
        d_vis_sub = cell.d_visible_sub
        elig_cell = cell.active_sub & (d_vis_sub > B_PX)
        b_cell = int(round(BUDGET_FULL * int(elig_cell.sum()) / elig_full_count))
        elig_noplaya = elig_cell & ~flat_playa[sl]

        # EXP-1: 100% label-free & 1m-LiDAR-free S_phys
        s1_sub = s_phys_full[sl]
        cells_exp1[cell.key] = emit_axial_crest_budget(
            np.power(np.clip(s1_sub, 0.0, 1.0), 3.0), elig_noplaya, budget=b_cell, min_sep_px=MIN_SEP_PX
        )

        # Fit pure-physical Dual-Cover models strictly inside foot & ~collars[cell.fold]
        train_dom = foot & ~collars[cell.fold]
        m_full, m_gap, q_tab = udsr.fit_dual_cover_models(
            train_dom,
            cell.visible_full,
            lid_valid,
            base_mm,
            udsr_mm,
            seed=SEED + idx_c * 17,
        )
        p_phys_sub = udsr.predict_dual_cover_bbox(
            sl, elig_cell, lid_valid, base_mm, udsr_mm, m_full, m_gap, q_tab
        )
        del m_full, m_gap
        vis_cont_sub = udsr.compute_visible_continuation(cell.visible_full, foot)[sl]
        gc.collect()

        # EXP-2: Single-stage Bayes-fused Dual-Cover OOF + Tip/Relay
        s2_sub = fuse_bayes_near(p_phys_sub, s1_sub, vis_cont_sub)
        cells_exp2[cell.key] = emit_axial_crest_budget(s2_sub, elig_noplaya, budget=b_cell, min_sep_px=MIN_SEP_PX)

        # EXP-3: Two-stage Stratified Residual Submodular (50% Bayes-fused near, 50% pure-physical far)
        s3_far = fuse_pure_far(p_phys_sub, s1_sub)
        m3, _ = emit_two_stage_stratified(
            s2_sub, s3_far, elig_noplaya, d_vis_sub, budget_total=b_cell, min_sep_px=MIN_SEP_PX, near_frac=0.50
        )
        cells_exp3[cell.key] = m3
        print(
            f"  [Holdout {idx_c+1}/8 {cell.key}] b_cell={b_cell} | "
            f"done in {time.time()-tc:.1f}s | RSS={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024:.0f} MiB"
        )

    hr1 = holdout.evaluate_hide_and_recover(cells_exp1, ctx, b_visible_px=B_PX, name="EXP-1_UDSR-PurePhysics")
    hr2 = holdout.evaluate_hide_and_recover(cells_exp2, ctx, b_visible_px=B_PX, name="EXP-2_UDSR-DualCover-OOF")
    hr3 = holdout.evaluate_hide_and_recover(cells_exp3, ctx, b_visible_px=B_PX, name="EXP-3_UDSR-Stratified-TwoRegime")
    print(f"[HR Results] EXP-1={hr1['pooled_dti']:.6f} | EXP-2={hr2['pooled_dti']:.6f} | EXP-3={hr3['pooled_dti']:.6f}")

    # Full-map 4-quadrant collared spatial OOF stitch for candidate rasters
    print("[Full-Map OOF] Building 4-quadrant collared spatial OOF pure-physical Dual-Cover surface...")
    p_phys_full = np.zeros(foot.shape, dtype=np.float32)
    for fold in holdout.FOLDS:
        tf = time.time()
        q_mask = (ctx.quad == fold) & foot
        sl_q = ctx.quad_bboxes[fold]
        train_dom = foot & ~collars[fold]
        vis_train_only = ctx.labels & train_dom
        m_full, m_gap, q_tab = udsr.fit_dual_cover_models(
            train_dom,
            vis_train_only,
            lid_valid,
            base_mm,
            udsr_mm,
            seed=SEED + 500 + fold * 31,
        )
        q_sub = q_mask[sl_q] & (d_cat_full[sl_q] > B_PX)
        pm_q = udsr.predict_dual_cover_bbox(
            sl_q, q_sub, lid_valid, base_mm, udsr_mm, m_full, m_gap, q_tab
        )
        p_phys_full[sl_q] = np.where(q_mask[sl_q], pm_q, p_phys_full[sl_q])
        del m_full, m_gap
        gc.collect()
        print(f"  [Full-Map Fold {fold+1}/4] {time.time()-tf:.1f}s")

    vis_cont_pub = udsr.compute_visible_continuation(ctx.labels, foot)
    elig_map_noplaya = foot_noplaya & (d_cat_full > B_PX)

    # Full-map EXP-1
    surf_exp1 = np.where(elig_map_noplaya, np.power(np.clip(s_phys_full, 0.0, 1.0), 3.0), 0.0).astype(np.float32)
    mask_exp1 = emit_axial_crest_budget(surf_exp1, elig_map_noplaya, budget=BUDGET_FULL, min_sep_px=MIN_SEP_PX)

    # Full-map EXP-2
    s2_raw = fuse_bayes_near(p_phys_full, s_phys_full, vis_cont_pub)
    surf_exp2 = np.where(elig_map_noplaya, np.clip(s2_raw / (float(s2_raw[elig_map_noplaya].max()) + 1e-6), 0.0, 1.0), 0.0).astype(np.float32)
    mask_exp2 = emit_axial_crest_budget(s2_raw, elig_map_noplaya, budget=BUDGET_FULL, min_sep_px=MIN_SEP_PX)

    # Full-map EXP-3
    s3_far_raw = fuse_pure_far(p_phys_full, s_phys_full)
    mask_exp3, st3_meta = emit_two_stage_stratified(
        s2_raw, s3_far_raw, elig_map_noplaya, d_cat_full, budget_total=BUDGET_FULL, min_sep_px=MIN_SEP_PX, near_frac=0.50
    )
    surf_exp3 = np.where(
        d_cat_full <= 15.0,
        udsr.rank01(s2_raw, elig_map_noplaya & (d_cat_full <= 15.0)),
        udsr.rank01(s3_far_raw, elig_map_noplaya & (d_cat_full > 15.0)),
    ).astype(np.float32)
    surf_exp3[~elig_map_noplaya] = 0.0
    del vis_cont_pub
    np.savez(
        wdir / "udsr_exp_checkpoint.npz",
        surf_exp1=surf_exp1,
        mask_exp1=mask_exp1.astype(np.uint8),
        surf_exp2=surf_exp2,
        mask_exp2=mask_exp2.astype(np.uint8),
        surf_exp3=surf_exp3,
        mask_exp3=mask_exp3.astype(np.uint8),
    )
    print(f"[Checkpoint] Saved full-map surfaces & masks at {time.time()-t0:.1f}s. Running 488-raster registry audits...")

    n_focus = len(fman["rasters"])
    exp_entries = []
    for exp_id, title, surf, mask, hr_rep in [
        ("EXP-1", "UDSR-PurePhysics", surf_exp1, mask_exp1, hr1),
        ("EXP-2", "UDSR-DualCover-OOF", surf_exp2, mask_exp2, hr2),
        ("EXP-3", "UDSR-Stratified-TwoRegime", surf_exp3, mask_exp3, hr3),
    ]:
        ta = time.time()
        sgmc_rep = holdout.evaluate_sgmc_with_ci(mask, ctx, name=f"{exp_id}_{title}")
        aud_surf_ext = registry_audit.audit_surface(surf, foot, eman, root=ROOT, template_tif=tpl_tif)
        aud_dots_ext = registry_audit.audit_final_dots(
            surf, mask, foot, eman, root=ROOT, template_tif=tpl_tif, space_filling_coverage=0.70
        )
        # Focus 442 is the exact prefix eman['rasters'][:n_focus] — derive exact focus summary without redundant I/O!
        focus_comps = aud_dots_ext["comparisons"][:n_focus]
        aud_dots_focus = {
            "passed": not any(bool(r.get("duplicate")) for r in focus_comps),
            "registry_rasters": len(focus_comps),
            "worst_within_3px_fraction": max(
                (float(r["within_3px_fraction"]) for r in focus_comps if r.get("within_3px_fraction") is not None),
                default=0.0,
            ),
            "worst_abs_spearman": max(
                (abs(float(r["spearman"])) for r in focus_comps if r.get("spearman") is not None),
                default=0.0,
            ),
            "comparisons": focus_comps,
        }
        prof = spatial_profile(mask, d_cat_full, lid_valid, flat_playa)
        sum_surf = summarize_surface_audit(aud_surf_ext)
        sum_focus = summarize_dots_audit(aud_dots_focus)
        sum_ext = summarize_dots_audit(aud_dots_ext)

        entry = {
            "experiment_id": exp_id,
            "name": title,
            "holdout_hide_and_recover": strip_private(hr_rep),
            "paired_vs_b2_static": paired_delta_from_boots(
                hr_rep["pooled_dti"], hr_rep["_boots"], rep_b2_static["pooled_dti"], rep_b2_static["_boots"]
            ),
            "paired_vs_b2_fold_honest": paired_delta_from_boots(
                hr_rep["pooled_dti"], hr_rep["_boots"], rep_b2_honest["pooled_dti"], rep_b2_honest["_boots"]
            ),
            "paired_vs_h19_5": paired_delta_from_boots(
                hr_rep["pooled_dti"], hr_rep["_boots"], rep_h19_honest["pooled_dti"], rep_h19_honest["_boots"]
            ),
            "holdout_sgmc_off_catalogue": strip_private(sgmc_rep),
            "paired_sgmc_cal_vs_b2": paired_delta_from_boots(
                sgmc_rep["sgmc_prevalence_calibrated_dti"],
                sgmc_rep["_cal_boots"],
                sgmc_b2["sgmc_prevalence_calibrated_dti"],
                sgmc_b2["_cal_boots"],
            ),
            "spatial_profile": prof,
            "registry_surface_audit_extended_488": sum_surf,
            "registry_dots_audit_focus_442": sum_focus,
            "registry_dots_audit_extended_488": sum_ext,
        }
        exp_entries.append((entry, surf, mask, aud_surf_ext, aud_dots_ext))
        print(
            f"[{exp_id} {title}] ({time.time()-ta:.1f}s) HR={hr_rep['pooled_dti']:.6f} "
            f"CI={[round(x,5) for x in hr_rep['ci95_cluster_bootstrap']]} | "
            f"d_vs_B2h={entry['paired_vs_b2_fold_honest']['delta_dti']:+.6f} "
            f"(CI+={entry['paired_vs_b2_fold_honest']['ci95_strictly_positive']}) | "
            f"SGMC_cal={sgmc_rep['sgmc_prevalence_calibrated_dti']:.6f} "
            f"(d_vs_B2={entry['paired_sgmc_cal_vs_b2']['delta_dti']:+.6f}) | "
            f">15px={prof['frac_d_gt_15px']*100:.1f}% | "
            f"max_sparse_3px={sum_ext['worst_sparse_within_3px']:.4f} | max_rho={sum_surf['worst_abs_spearman']:.4f}"
        )

    eligible = []
    for entry, surf, mask, aud_s, aud_d in exp_entries:
        gates_ok = (
            aud_s["passed"]
            and aud_d["passed"]
            and entry["paired_vs_b2_static"]["ci95_strictly_positive"]
            and entry["paired_vs_b2_fold_honest"]["ci95_strictly_positive"]
            and entry["spatial_profile"]["frac_d_gt_15px"] >= 0.35
        )
        entry["all_promotion_gates_passed"] = bool(gates_ok)
        if gates_ok:
            eligible.append((entry, surf, mask, aud_s, aud_d))

    if eligible:
        chosen = next((t for t in eligible if t[0]["experiment_id"] == "EXP-3"), eligible[-1])
        verdict = "promote"
    else:
        chosen = exp_entries[-1]
        verdict = "negative"

    win_entry, win_surf, win_mask, win_aud_s, win_aud_d = chosen
    np.savez_compressed(
        wdir / "promoted_udsr.npz",
        experiment_id=win_entry["experiment_id"],
        verdict=verdict,
        belief=win_surf.astype(np.float32),
        mask=win_mask.astype(np.uint8),
    )
    (ROOT / "evidence").mkdir(exist_ok=True)
    # Save compact audit reports without 488-row bloat (full top-25 preserved)
    win_s_slim = {k: v for k, v in win_aud_s.items() if k != "comparisons"}
    win_s_slim["top25_comparisons"] = sorted(
        [r for r in win_aud_s["comparisons"] if r.get("spearman") is not None],
        key=lambda r: -abs(float(r["spearman"])),
    )[:25]
    win_d_slim = {k: v for k, v in win_aud_d.items() if k != "comparisons"}
    win_d_slim["top25_sparse_comparisons"] = sorted(
        [r for r in win_aud_d["comparisons"] if r.get("within_3px_fraction") is not None and not r.get("space_filling")],
        key=lambda r: -float(r["within_3px_fraction"]),
    )[:25]
    (ROOT / "evidence/udsr_surface_audit.json").write_text(json.dumps(win_s_slim, indent=2) + "\n")
    (ROOT / "evidence/udsr_dots_audit.json").write_text(json.dumps(win_d_slim, indent=2) + "\n")

    summary = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.time() - t0, 2),
        "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1),
        "experiment_budget_used": 3,
        "experiment_budget_max": 3,
        "baselines": {
            "GEMSDOE32_B2_static_holdout": strip_private(rep_b2_static),
            "D28_B2_fold_honest_holdout": strip_private(rep_b2_honest),
            "H19_5_fold_honest_holdout": strip_private(rep_h19_honest),
            "GEMSDOE32_B2_sgmc_off_catalogue": strip_private(sgmc_b2),
        },
        "experiments": [e[0] for e in exp_entries],
        "selected_experiment": win_entry["experiment_id"],
        "verdict": verdict,
        "stage3_meta": st3_meta,
    }
    out_json = ROOT / "evidence/udsr_three_experiments_20261027.json"
    out_json.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\n[DONE] Selected={win_entry['experiment_id']} ({verdict}) in {summary['elapsed_seconds']}s -> {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
