#!/usr/bin/env python3
"""Execute the 3 pre-registered H-SPMD experiments (knowledge/preregistration_spmd_20261028.md).

Method lane: SAR-PU Mapping-Propensity De-confounding & Shallow Matched-Depth /
Epithermal Conduit Inversion (61-channel M_Full + 55-channel M_Gap Dual-Cover +
39-channel DEM/LiDAR-free subsurface spy teacher).

  EXP-1 (SPMD-Sup61-Ctrl)    : Supervised 61/55-ch Dual-Cover + Bayes tip/relay fusion,
                               single-stage axial crest emit (budget=34500, min_sep=3.05, support_mult=6.8).
  EXP-2 (SPMD-SARPU-Unified) : SAR-PU spy-purified + propensity-weighted 61/55-ch Dual-Cover +
                               Bayes tip/relay fusion (budget=34500, min_sep=3.05, support_mult=6.8).
  EXP-3 (SPMD-SARPU-TwoRegime): Two-regime residual submodular SAR-PU emit (budget=33600, min_sep=3.12,
                               support_mult=6.8): 64% Bayes-fused corridor (2 < d <= 18 px) +
                               36% propensity-deconfounded subsurface far-field (d > 18 px).

Reuses canonical ``gems32.holdout``, ``gems32.emitter``, ``gems32.registry_audit``,
``gems32.udsr``, and ``gems32.spmd`` modules. Legacy superseded entry points remain
fail-closed in ``scripts/experiment_guard.py``.
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

from gems32 import holdout, paths, registry_audit, spmd, udsr  # noqa: E402
from run_udsr_experiments import (  # noqa: E402
    emit_axial_crest_budget,
    paired_delta_from_boots,
    spatial_profile,
    strip_private,
    summarize_dots_audit,
    summarize_surface_audit,
)

B_PX = 2.0
CORRIDOR_PX = 18.0
SUPPORT_MULT = 6.8
BUDGET_UNIFIED = 34500
MIN_SEP_UNIFIED = 3.05
BUDGET_TWOREG = 33600
MIN_SEP_TWOREG = 3.12
NEAR_FRAC_TWOREG = 0.64
GAMMA_TRAIN = 0.38
SEED = 20261028
ARCHIVED_BEST_HR = 0.113696       # H-UDSR EXP-2 (failed sparse overlap at 80.62%)
ARCHIVED_BEST_UNIQUE_HR = 0.094698  # H-UDSR EXP-3 (passed sparse overlap at 69.42%)


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def fuse_corridor(
    post: np.ndarray,
    ehat: np.ndarray,
    sub_conduit: np.ndarray,
    vis_cont_sub: np.ndarray,
    deconf_pow: float = 0.0,
    relay_w: float = 3.0,
    tip_w: float = 2.2,
) -> np.ndarray:
    """Bayes-fused Dual-Cover posterior + pure-subsurface conduit + fold-visible continuation."""
    p_eff = np.clip(post / np.power(np.clip(ehat, 0.22, 1.0), deconf_pow), 0.0, 1.0)
    base_p = 0.86 * np.power(p_eff, 1.3) + 0.14 * np.power(np.clip(sub_conduit, 0.0, 1.0), 2.5)
    prior_mult = 1.0 + relay_w * vis_cont_sub[:, :, 1] + tip_w * vis_cont_sub[:, :, 0]
    return (base_p * prior_mult).astype(np.float32)


def fuse_sarpu_farfield(
    post: np.ndarray,
    ehat: np.ndarray,
    sub_conduit: np.ndarray,
    deconf_pow: float = 0.42,
) -> np.ndarray:
    """Zero-catalogue propensity-deconfounded subsurface SAR-PU far-field surface (d > 18 px)."""
    p_deconf = np.clip(post / np.power(np.clip(ehat, 0.22, 1.0), deconf_pow), 0.0, 1.0)
    return (
        0.74 * np.power(p_deconf, 1.35)
        + 0.26 * np.power(np.clip(sub_conduit, 0.0, 1.0), 2.4)
    ).astype(np.float32)


def emit_sarpu_two_regime(
    s_near: np.ndarray,
    s_far: np.ndarray,
    foot_elig: np.ndarray,
    d_vis: np.ndarray,
    budget_total: int,
    min_sep_px: float = MIN_SEP_TWOREG,
    near_frac: float = NEAR_FRAC_TWOREG,
    support_mult: float = SUPPORT_MULT,
) -> tuple[np.ndarray, dict]:
    """Two-regime residual submodular placement across 2 < d <= 18 px and d > 18 px."""
    b_near = int(round(budget_total * near_frac))
    b_far = int(budget_total - b_near)

    dom_near = foot_elig & (d_vis > B_PX) & (d_vis <= CORRIDOR_PX)
    mask_a = emit_axial_crest_budget(
        s_near, dom_near, budget=b_near, min_sep_px=min_sep_px, support_mult=support_mult
    )

    dom_far = foot_elig & (d_vis > CORRIDOR_PX)
    mask_b = emit_axial_crest_budget(
        s_far,
        dom_far,
        budget=b_far,
        min_sep_px=min_sep_px,
        initial_mask=mask_a,
        support_mult=support_mult,
    )
    mask = mask_a | mask_b
    return mask, {
        "n_near_emitted": int(mask_a.sum()),
        "n_far_emitted": int(mask_b.sum()),
        "n_total_emitted": int(mask.sum()),
        "corridor_px": CORRIDOR_PX,
        "near_frac_target": near_frac,
    }


def main() -> int:
    t0 = time.time()
    ddir = paths.data_dir()
    wdir = paths.work_dir()
    tpl_tif = ddir / "sample_submission.tif"

    info = spmd.build_spmd_stack(ddir, wdir, force=False, log=log)
    foot = info["foot"]
    lid_valid = info["lidar_valid"]
    flat_playa = info["flat_deep_playa"]
    foot_noplaya = foot & ~flat_playa
    sub_conduit_full = np.load(info["sub_conduit_path"]).astype(np.float32)

    ctx = holdout.load_holdout_context(ddir)
    base_mm = open_memmap(wdir / "feature_stack_35.npy", mode="r")
    udsr_mm = open_memmap(wdir / "udsr_stack_18.npy", mode="r")
    spmd_mm = open_memmap(wdir / "spmd_stack_8.npy", mode="r")

    # Gate 1: Verify 63-channel leakage canary (load cached if already executed, else run)
    canary_path = ROOT / "evidence/spmd_leakage_canary_63ch.json"
    if canary_path.is_file():
        canary = json.loads(canary_path.read_text())
    else:
        canary = spmd.run_leakage_canary_63ch(base_mm, udsr_mm, spmd_mm, ctx)
        canary_path.write_text(json.dumps(canary, indent=2) + "\n")
    log(f"[Canary 63ch] passed={canary['passed']} max_oriented_auc={canary['max_oriented_auc']} "
        f"worst={canary['worst_channel']}")
    if not canary["passed"]:
        log("[STOP] 63-channel leakage canary failed (oriented AUC > 0.90); aborting.")
        return 2

    d_cat_full = distance_transform_edt(~ctx.labels).astype(np.float32)
    elig_full_count = int((foot & (d_cat_full > B_PX)).sum())
    collars = {
        fold: binary_dilation(ctx.quad == fold, structure=np.ones((3, 3), bool),
                              iterations=holdout.COLLAR_PX) & foot
        for fold in holdout.FOLDS
    }

    # Evaluate shared controls (never counted against 3-experiment budget)
    eman = json.loads((ROOT / "registry/extended_registry_manifest.json").read_text())
    b2_entry = next(e for e in eman["rasters"] if e.get("sha256", "").startswith("c55bafc4"))
    b2_mask = holdout.read_binary(ROOT / b2_entry["local"])
    d28_mask = holdout.read_binary(ddir / "scored/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif")
    udsr_e3_mask = holdout.read_binary(
        ROOT / "docs/downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif"
    )
    rep_b2_static = holdout.evaluate_hide_and_recover(b2_mask, ctx, b_visible_px=0.0, name="GEMSDOE32_B2_static")
    rep_b2_honest = holdout.evaluate_hide_and_recover(d28_mask, ctx, b_visible_px=2.0, name="D28_B2_fold_honest")
    rep_udsr_e3_static = holdout.evaluate_hide_and_recover(
        udsr_e3_mask, ctx, b_visible_px=2.0, name="UDSR_EXP3_static_oof"
    )
    sgmc_b2 = holdout.evaluate_sgmc_with_ci(b2_mask, ctx, name="GEMSDOE32_B2")
    log(f"[Baselines] B2 static={rep_b2_static['pooled_dti']:.6f} | "
        f"D28_B2 fold-honest={rep_b2_honest['pooled_dti']:.6f} | "
        f"B2 SGMC_cal={sgmc_b2['sgmc_prevalence_calibrated_dti']:.6f}")

    # ---- Execute 8-cell Hide-and-Recover across EXP-1, EXP-2, EXP-3 ----
    force_rerun = "--force" in sys.argv
    hr_ckpt = wdir / "spmd_hr_checkpoint.json"
    if hr_ckpt.is_file() and not force_rerun:
        log(f"[HR] Loading deterministic 8-cell holdout checkpoint from {hr_ckpt.name}...")
        ck = json.loads(hr_ckpt.read_text())
        purged_fracs = ck["purged_fracs"]
        hr = ck["hr"]
        for k in hr:
            hr[k]["_boots"] = np.asarray(hr[k]["_boots"], dtype=np.float64)
    else:
        cells = {"EXP-1": {}, "EXP-2": {}, "EXP-3": {}}
        purged_fracs = []
        for idx_c, cell in enumerate(ctx.cells):
            tc = time.time()
            sl = cell.bbox
            d_vis_sub = cell.d_visible_sub
            elig_cell = cell.active_sub & (d_vis_sub > B_PX)
            elig_noplaya = elig_cell & ~flat_playa[sl]
            b_cell_unif = int(round(BUDGET_UNIFIED * int(elig_cell.sum()) / elig_full_count))
            b_cell_twor = int(round(BUDGET_TWOREG * int(elig_cell.sum()) / elig_full_count))

            train_dom = foot & ~collars[cell.fold]
            sub_sub = sub_conduit_full[sl]
            vis_cont_sub = udsr.compute_visible_continuation(cell.visible_full, foot)[sl]

            # 1) Supervised 61/55-ch Dual-Cover for EXP-1
            b_sup = spmd.fit_dual_cover_61(
                train_dom, cell.visible_full, lid_valid, base_mm, udsr_mm, spmd_mm,
                sarpu=False, seed=SEED + idx_c * 17,
            )
            p_sup, e_sup = spmd.predict_dual_cover_61_bbox(
                sl, elig_cell, lid_valid, base_mm, udsr_mm, spmd_mm, b_sup
            )
            del b_sup
            s1_sub = fuse_corridor(p_sup, e_sup, sub_sub, vis_cont_sub, deconf_pow=0.0)
            cells["EXP-1"][cell.key] = emit_axial_crest_budget(
                s1_sub, elig_noplaya, budget=b_cell_unif, min_sep_px=MIN_SEP_UNIFIED, support_mult=SUPPORT_MULT
            )
            del p_sup, e_sup, s1_sub
            gc.collect()

            # 2) SAR-PU 61/55-ch Dual-Cover shared cleanly by EXP-2 and EXP-3
            b_sar = spmd.fit_dual_cover_61(
                train_dom, cell.visible_full, lid_valid, base_mm, udsr_mm, spmd_mm,
                sarpu=True, gamma_train=GAMMA_TRAIN, seed=SEED + idx_c * 17,
            )
            purged_fracs.append(b_sar["purged_unlabeled_fraction"])
            p_sar, e_sar = spmd.predict_dual_cover_61_bbox(
                sl, elig_cell, lid_valid, base_mm, udsr_mm, spmd_mm, b_sar
            )
            del b_sar

            s2_sub = fuse_corridor(p_sar, e_sar, sub_sub, vis_cont_sub, deconf_pow=0.22)
            cells["EXP-2"][cell.key] = emit_axial_crest_budget(
                s2_sub, elig_noplaya, budget=b_cell_unif, min_sep_px=MIN_SEP_UNIFIED, support_mult=SUPPORT_MULT
            )
            del s2_sub

            s3_near = fuse_corridor(
                p_sar, e_sar, sub_sub, vis_cont_sub, deconf_pow=0.18, relay_w=2.8, tip_w=2.0
            )
            s3_far = fuse_sarpu_farfield(p_sar, e_sar, sub_sub, deconf_pow=0.42)
            m3, _ = emit_sarpu_two_regime(
                s3_near, s3_far, elig_noplaya, d_vis_sub,
                budget_total=b_cell_twor, min_sep_px=MIN_SEP_TWOREG, near_frac=NEAR_FRAC_TWOREG,
            )
            cells["EXP-3"][cell.key] = m3
            del p_sar, e_sar, s3_near, s3_far, vis_cont_sub
            gc.collect()
            log(f"  [Holdout {idx_c+1}/8 {cell.key}] b_unif={b_cell_unif} b_twor={b_cell_twor} "
                f"n1={int(cells['EXP-1'][cell.key].sum())} n2={int(cells['EXP-2'][cell.key].sum())} "
                f"n3={int(cells['EXP-3'][cell.key].sum())} | {time.time()-tc:.1f}s | "
                f"RSS={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024:.0f} MiB")

        hr = {
            "EXP-1": holdout.evaluate_hide_and_recover(cells["EXP-1"], ctx, b_visible_px=B_PX, name="EXP-1_SPMD-Sup61-Ctrl"),
            "EXP-2": holdout.evaluate_hide_and_recover(cells["EXP-2"], ctx, b_visible_px=B_PX, name="EXP-2_SPMD-SARPU-Unified"),
            "EXP-3": holdout.evaluate_hide_and_recover(cells["EXP-3"], ctx, b_visible_px=B_PX, name="EXP-3_SPMD-SARPU-TwoRegime"),
        }
        del cells
        gc.collect()
        hr_serial = {}
        for k, v in hr.items():
            d = strip_private(v)
            d["_boots"] = [float(x) for x in v["_boots"]]
            hr_serial[k] = d
        hr_ckpt.write_text(json.dumps({"purged_fracs": purged_fracs, "hr": hr_serial}) + "\n")

    for k, v in hr.items():
        tot_emit = sum(int(f["emitted"]) for f in v["folds"].values())
        tot_tp = sum(float(f["tp"]) for f in v["folds"].values())
        log(f"[HR] {k} pooled HOLDOUT-DTI={v['pooled_dti']:.6f} "
            f"CI={[round(x, 5) for x in v['ci95_cluster_bootstrap']]} "
            f"sum_emit={tot_emit} tp/dot={tot_tp/max(tot_emit,1):.4f}")

    # ---- Full-Map 4-Quadrant Collared Spatial OOF Stitch ----
    exp_ckpt = wdir / "spmd_exp_checkpoint.npz"
    if exp_ckpt.is_file() and not force_rerun:
        log(f"[Full-Map OOF] Loading saved 4-quadrant OOF surfaces/masks from {exp_ckpt.name}...")
        npz = np.load(exp_ckpt)
        surfaces = {k: npz[f"surf_{k}"].astype(np.float32) for k in ("EXP-1", "EXP-2", "EXP-3")}
        masks = {k: npz[f"mask_{k}"].astype(bool) for k in ("EXP-1", "EXP-2", "EXP-3")}
        d_m3 = d_cat_full[masks["EXP-3"]]
        st3_meta = {
            "n_near_emitted": int(((d_m3 > B_PX) & (d_m3 <= CORRIDOR_PX)).sum()),
            "n_far_emitted": int((d_m3 > CORRIDOR_PX).sum()),
            "n_total_emitted": int(masks["EXP-3"].sum()),
            "corridor_px": CORRIDOR_PX,
            "near_frac_target": NEAR_FRAC_TWOREG,
        }
        for eid in ("EXP-1", "EXP-2", "EXP-3"):
            log(f"[Full-Map {eid}] loaded {int(masks[eid].sum())} dots")
    else:
        log("[Full-Map OOF] Building 4-quadrant collared spatial OOF surfaces (Sup61 & SAR-PU)...")
        p_sup_full = np.zeros(foot.shape, dtype=np.float32)
        p_sar_full = np.zeros(foot.shape, dtype=np.float32)
        e_sar_full = np.ones(foot.shape, dtype=np.float32)

        for fold in holdout.FOLDS:
            tf = time.time()
            q_mask = (ctx.quad == fold) & foot
            sl_q = ctx.quad_bboxes[fold]
            train_dom = foot & ~collars[fold]
            vis_train_only = ctx.labels & train_dom
            q_sub = q_mask[sl_q] & (d_cat_full[sl_q] > B_PX)

            b_sup_q = spmd.fit_dual_cover_61(
                train_dom, vis_train_only, lid_valid, base_mm, udsr_mm, spmd_mm,
                sarpu=False, seed=SEED + 500 + fold * 31,
            )
            ps_q, _ = spmd.predict_dual_cover_61_bbox(
                sl_q, q_sub, lid_valid, base_mm, udsr_mm, spmd_mm, b_sup_q
            )
            p_sup_full[sl_q] = np.where(q_mask[sl_q], ps_q, p_sup_full[sl_q])
            del b_sup_q, ps_q
            gc.collect()

            b_sar_q = spmd.fit_dual_cover_61(
                train_dom, vis_train_only, lid_valid, base_mm, udsr_mm, spmd_mm,
                sarpu=True, gamma_train=GAMMA_TRAIN, seed=SEED + 500 + fold * 31,
            )
            pr_q, eh_q = spmd.predict_dual_cover_61_bbox(
                sl_q, q_sub, lid_valid, base_mm, udsr_mm, spmd_mm, b_sar_q
            )
            p_sar_full[sl_q] = np.where(q_mask[sl_q], pr_q, p_sar_full[sl_q])
            e_sar_full[sl_q] = np.where(q_mask[sl_q], eh_q, e_sar_full[sl_q])
            del b_sar_q, pr_q, eh_q
            gc.collect()
            log(f"  [Full-Map Fold {fold+1}/4] {time.time()-tf:.1f}s "
                f"RSS={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024:.0f} MiB")

        vis_cont_pub = udsr.compute_visible_continuation(ctx.labels, foot)
        elig_map = foot_noplaya & (d_cat_full > B_PX)
        ones_e = np.ones_like(p_sup_full)

        # Full-Map EXP-1
        s1_raw = fuse_corridor(p_sup_full, ones_e, sub_conduit_full, vis_cont_pub, deconf_pow=0.0)
        del p_sup_full, ones_e
        mask_exp1 = emit_axial_crest_budget(
            s1_raw, elig_map, budget=BUDGET_UNIFIED, min_sep_px=MIN_SEP_UNIFIED, support_mult=SUPPORT_MULT
        )
        surf_exp1 = np.where(
            elig_map, np.clip(s1_raw / max(float(s1_raw[elig_map].max()), 1e-6), 0.0, 1.0), 0.0
        ).astype(np.float32)
        del s1_raw

        # Full-Map EXP-2
        s2_raw = fuse_corridor(p_sar_full, e_sar_full, sub_conduit_full, vis_cont_pub, deconf_pow=0.22)
        mask_exp2 = emit_axial_crest_budget(
            s2_raw, elig_map, budget=BUDGET_UNIFIED, min_sep_px=MIN_SEP_UNIFIED, support_mult=SUPPORT_MULT
        )
        surf_exp2 = np.where(
            elig_map, np.clip(s2_raw / max(float(s2_raw[elig_map].max()), 1e-6), 0.0, 1.0), 0.0
        ).astype(np.float32)
        del s2_raw

        # Full-Map EXP-3
        s3_near_raw = fuse_corridor(
            p_sar_full, e_sar_full, sub_conduit_full, vis_cont_pub, deconf_pow=0.18, relay_w=2.8, tip_w=2.0
        )
        s3_far_raw = fuse_sarpu_farfield(p_sar_full, e_sar_full, sub_conduit_full, deconf_pow=0.42)
        del p_sar_full, e_sar_full, vis_cont_pub
        mask_exp3, st3_meta = emit_sarpu_two_regime(
            s3_near_raw, s3_far_raw, elig_map, d_cat_full,
            budget_total=BUDGET_TWOREG, min_sep_px=MIN_SEP_TWOREG, near_frac=NEAR_FRAC_TWOREG,
        )
        near_dom = elig_map & (d_cat_full <= CORRIDOR_PX)
        far_dom = elig_map & (d_cat_full > CORRIDOR_PX)
        nmax = max(float(s3_near_raw[near_dom].max()) if near_dom.any() else 1.0, 1e-6)
        fmax = max(float(s3_far_raw[far_dom].max()) if far_dom.any() else 1.0, 1e-6)
        surf_exp3 = np.where(
            d_cat_full <= CORRIDOR_PX,
            np.where(elig_map, np.clip(s3_near_raw / nmax, 0.0, 1.0), 0.0),
            np.where(elig_map, np.clip(s3_far_raw / fmax, 0.0, 1.0), 0.0),
        ).astype(np.float32)
        del s3_near_raw, s3_far_raw
        gc.collect()

        surfaces = {"EXP-1": surf_exp1, "EXP-2": surf_exp2, "EXP-3": surf_exp3}
        masks = {"EXP-1": mask_exp1, "EXP-2": mask_exp2, "EXP-3": mask_exp3}
        for eid in ("EXP-1", "EXP-2", "EXP-3"):
            log(f"[Full-Map {eid}] emitted {int(masks[eid].sum())} dots")

        np.savez(
            exp_ckpt,
            **{f"surf_{k}": surfaces[k] for k in surfaces},
            **{f"mask_{k}": masks[k].astype(np.uint8) for k in masks},
        )

    # ---- SGMC diagnostic + 549-raster Extended Registry Audits ----
    titles = {
        "EXP-1": "SPMD-Sup61-Ctrl",
        "EXP-2": "SPMD-SARPU-Unified",
        "EXP-3": "SPMD-SARPU-TwoRegime",
    }
    entries = []
    for exp_id in ("EXP-1", "EXP-2", "EXP-3"):
        ta = time.time()
        title = titles[exp_id]
        sg = holdout.evaluate_sgmc_with_ci(masks[exp_id], ctx, name=f"{exp_id}_{title}")
        hr_static_oof = holdout.evaluate_hide_and_recover(
            masks[exp_id], ctx, b_visible_px=B_PX, name=f"{exp_id}_{title}_static_oof"
        )
        aud_s = registry_audit.audit_surface(
            surfaces[exp_id], foot, eman, root=ROOT, template_tif=tpl_tif
        )
        aud_d = registry_audit.audit_final_dots(
            surfaces[exp_id], masks[exp_id], foot, eman,
            root=ROOT, template_tif=tpl_tif, space_filling_coverage=0.70,
        )
        sum_s = summarize_surface_audit(aud_s)
        sum_d = summarize_dots_audit(aud_d)
        sum_d["literal_rule_passed"] = aud_d["literal_rule_passed"]
        sum_d["audit_complete"] = aud_d["audit_complete"]
        sum_d["malformed_or_missing"] = aud_d["malformed_or_missing"]
        sum_s["audit_complete"] = aud_s["audit_complete"]
        sum_s["malformed_or_missing"] = aud_s["malformed_or_missing"]

        sp_prof = spatial_profile(masks[exp_id], d_cat_full, lid_valid, flat_playa)
        d_m = d_cat_full[masks[exp_id]]
        sp_prof["frac_d_2_to_18px"] = round(float(((d_m > 2.0) & (d_m <= 18.0)).mean()), 5)
        sp_prof["frac_d_gt_18px"] = round(float((d_m > 18.0).mean()), 5)

        p_vs_b2h = paired_delta_from_boots(
            hr[exp_id]["pooled_dti"], hr[exp_id]["_boots"],
            rep_b2_honest["pooled_dti"], rep_b2_honest["_boots"],
        )
        p_vs_exp1 = paired_delta_from_boots(
            hr[exp_id]["pooled_dti"], hr[exp_id]["_boots"],
            hr["EXP-1"]["pooled_dti"], hr["EXP-1"]["_boots"],
        )
        sparse_unique = bool(sum_s["passed"] and sum_d["passed"])
        beats_repo_best = bool(hr[exp_id]["pooled_dti"] > ARCHIVED_BEST_HR)
        beats_unique_best = bool(hr[exp_id]["pooled_dti"] > ARCHIVED_BEST_UNIQUE_HR)

        entry = {
            "experiment_id": exp_id,
            "name": title,
            "holdout_hide_and_recover": strip_private(hr[exp_id]),
            "static_fullmap_oof_holdout": {
                "pooled_dti": hr_static_oof["pooled_dti"],
                "ci95_cluster_bootstrap": hr_static_oof["ci95_cluster_bootstrap"],
                "note": "Saved full-map OOF mask re-scored statically across ctx.cells to verify zero fold-to-fullmap collapse.",
            },
            "paired_vs_d28_b2_fold_honest": p_vs_b2h,
            "paired_vs_exp1_ctrl": p_vs_exp1,
            "sgmc_diagnostic": strip_private(sg),
            "spatial_profile": sp_prof,
            "two_stage_meta": st3_meta if exp_id == "EXP-3" else None,
            "surface_audit": sum_s,
            "dots_audit": sum_d,
            "gates": {
                "G1_leakage_canary_63ch": bool(canary["passed"]),
                "G2a_beats_d28_b2_paired_ci": bool(p_vs_b2h["ci95_strictly_positive"]),
                "G2b_beats_archived_unique_best_00947": beats_unique_best,
                "G2c_beats_archived_all_best_01137": beats_repo_best,
                "G3a_sparse_uniqueness_543_rasters": sparse_unique,
                "G3b_literal_all_including_13gemsdoe_lattice": bool(aud_d["literal_rule_passed"]),
            },
        }
        entries.append(entry)
        log(f"[{exp_id} {title}] {time.time()-ta:.1f}s | HR={hr[exp_id]['pooled_dti']:.6f} "
            f"(static_oof={hr_static_oof['pooled_dti']:.6f}) | "
            f"d_vs_D28={p_vs_b2h['delta_dti']:+.6f} CI={p_vs_b2h['ci95_paired_cluster_bootstrap']} | "
            f"SGMC_cal={sg['sgmc_prevalence_calibrated_dti']:.6f} | "
            f"max|rho|={sum_s['worst_abs_spearman']} | "
            f"worst_sparse3px={sum_d['worst_sparse_within_3px']} ({sum_d['worst_sparse_raster']}) | "
            f"literal_pass={aud_d['literal_rule_passed']}")

    # Local prior-candidate overlap within this repository
    local_overlaps = {}
    for lname, fn in (
        ("AP-1", "apartgemsdoe2-ap1-dilatcond-37654-20261027-1f26aa05-zeros.tif"),
        ("AP2", "apartgemsdoe2-ap2-oofctrl-44090dots-20261027T220804Z-5e265df9-zeros.tif"),
        ("H-UDSR-EXP3", "apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif"),
        ("H-TRACE-EXP1", "apartgemsdoe2-trace-exp1-ctrl-t0-27236-20261028T064500Z-5e69619b-zeros.tif"),
    ):
        p_loc = ROOT / "docs/downloads" / fn
        if p_loc.is_file():
            m_loc = holdout.read_binary(p_loc) & foot
            dm = distance_transform_edt(~m_loc)
            local_overlaps[lname] = {
                eid: round(float((dm[masks[eid]] <= 3.0).mean()), 6) for eid in masks
            }
            local_overlaps[lname]["dots"] = int(m_loc.sum())

    sparse_passing = [e for e in entries if e["gates"]["G3a_sparse_uniqueness_543_rasters"]]
    selected = (
        max(sparse_passing, key=lambda e: e["holdout_hide_and_recover"]["pooled_dti"])
        if sparse_passing
        else max(entries, key=lambda e: e["holdout_hide_and_recover"]["pooled_dti"])
    )

    summary = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.time() - t0, 2),
        "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1),
        "experiment_budget_used": 3,
        "experiment_budget_max": 3,
        "lane": "H-SPMD (knowledge/preregistration_spmd_20261028.md)",
        "sarpu_mean_purged_unlabeled_fraction": round(float(np.mean(purged_fracs)), 5),
        "canary_63ch_summary": {
            "passed": canary["passed"],
            "n_features_tested": canary["n_features_tested"],
            "max_oriented_auc": canary["max_oriented_auc"],
            "worst_channel": canary["worst_channel"],
            "spmd_new_8ch_aucs": canary["spmd_new_8ch_aucs"],
        },
        "baselines": {
            "GEMSDOE32_B2_static_holdout": strip_private(rep_b2_static),
            "D28_B2_fold_honest_holdout": strip_private(rep_b2_honest),
            "UDSR_EXP3_static_oof_holdout": strip_private(rep_udsr_e3_static),
            "GEMSDOE32_B2_sgmc": strip_private(sgmc_b2),
            "archived_repo_best_hr_hudsr_exp2": ARCHIVED_BEST_HR,
            "archived_repo_best_sparse_unique_hr_hudsr_exp3": ARCHIVED_BEST_UNIQUE_HR,
        },
        "experiments": entries,
        "local_prior_candidate_overlap_within3px": local_overlaps,
        "selected_candidate_id": selected["experiment_id"],
        "best_by_raw_holdout": max(entries, key=lambda e: e["holdout_hide_and_recover"]["pooled_dti"])["experiment_id"],
    }
    out_path = ROOT / "evidence/spmd_three_experiments_20261028.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n")
    log(f"[DONE] selected={selected['experiment_id']} best_raw={summary['best_by_raw_holdout']} "
        f"in {summary['elapsed_seconds']}s (peak RSS {summary['peak_rss_mib']} MiB) -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
