#!/usr/bin/env python3
"""Execute the 3 pre-registered H-TRACE experiments (knowledge/preregistration_trace_20261028.md).

Lane: reshape the leak-free H-UDSR Dual-Cover OOF posterior by km-scale oriented
trace coherence (``gems32.trace``), then emit with the shared axial-crest exact-gain
emitter at the historical 37,654-dot budget, B=2 px visible-catalogue collar.

  EXP-1 CTRL-T0 : posterior F0 alone.
  EXP-2 TRACE-T1: F0 * (0.2 + 0.8 * Tn), Tn = two-scale trace coherence / p99.5.
  EXP-3 TRACE-T2: EXP-2 field restricted to hysteresis (oriented-closing) support.

Evaluation reuses the shared modules only: ``gems32.holdout``
(GEMSDOE32-HIDE-RECOVER-v3.0 pooled DTI + cluster-bootstrap CI; SGMC-CAL-v3.0 as a
labelled secondary diagnostic), ``gems32.udsr`` Dual-Cover fits, and
``gems32.registry_audit`` for surface/final-dot uniqueness vs the extended registry.
No registry/champion pixel is read as a model input; scored rasters are read only
as holdout controls and for the uniqueness measurement.

This is a NEW session entry point (2026-10-28, arena/7ec4400f) under the user's
explicit "work on the next steps from the previous sessions first" instruction;
the legacy fail-closed guard in ``scripts/experiment_guard.py`` continues to block
the superseded AP-1/AP2/H-UDSR entry points and is not weakened here.
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
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems32 import holdout, paths, registry_audit, trace, udsr  # noqa: E402
from run_udsr_experiments import emit_axial_crest_budget, paired_delta_from_boots, strip_private  # noqa: E402

BUDGET_FULL = 37654
MIN_SEP_PX = 2.9
B_PX = 2.0
SEED = 20261028
CURRENT_BEST_HR = 0.113696  # H-UDSR EXP-2, evidence/udsr_three_experiments_20261027.json


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def exp3_field(field2: np.ndarray, posterior: np.ndarray, domain: np.ndarray,
               budget: int) -> np.ndarray:
    """Hysteresis-restricted EXP-2 field (seeds mirror the emitter support rule)."""
    crest = udsr.is_crest_4az(field2, domain) & domain
    cand = crest if int(crest.sum()) >= budget * 2 else domain
    vals = np.nan_to_num(field2[cand], nan=0.0)
    k = min(vals.size, max(int(round(budget * 3.6)), budget + 500))
    thr = float(vals.min()) if k >= vals.size else float(np.partition(vals, -k)[-k])
    seeds = cand & (field2 >= thr)
    support = trace.hysteresis_support(seeds, domain)
    top_post = domain & (posterior >= float(np.quantile(posterior[domain][::4], 0.999)))
    support |= top_post
    return np.where(support, field2, 0.0).astype(np.float32)


def fields_for(posterior: np.ndarray, foot_sub: np.ndarray) -> tuple[dict, dict]:
    """Build EXP-1/2/3 emission fields for one bbox (EXP-3 needs a budget later)."""
    coh = trace.trace_coherence(posterior, foot_sub)
    tn = trace.normalise_p995(coh["t_geo"], foot_sub)
    f1 = np.where(foot_sub, np.clip(posterior, 0.0, 1.0), 0.0).astype(np.float32)
    f2 = trace.trace_gate_field(posterior, tn, foot_sub, floor=0.2)
    return {"f1": f1, "f2": f2, "tn": tn}, {"tau": coh["tau"]}


def spatial_profile(mask: np.ndarray, d_cat: np.ndarray) -> dict:
    d = d_cat[mask]
    return {
        "n_dots": int(mask.sum()),
        "frac_d_le_2px": round(float((d <= 2.0).mean()), 5),
        "frac_d_2_to_15px": round(float(((d > 2.0) & (d <= 15.0)).mean()), 5),
        "frac_d_gt_15px": round(float((d > 15.0).mean()), 5),
    }


def canary_trace_fields(ctx, s_phys: np.ndarray, foot: np.ndarray, d_cat: np.ndarray) -> dict:
    """Single-feature leakage canary for label-free trace fields derived from S_phys."""
    coh = trace.trace_coherence(s_phys, foot)
    pos_mask = np.zeros(foot.shape, bool)
    for cell in ctx.cells:
        sl = cell.bbox
        sub = np.zeros((sl[0].stop - sl[0].start, sl[1].stop - sl[1].start), bool)
        sub[cell.truth_coords] = True
        pos_mask[sl] |= sub
    rng = np.random.default_rng(SEED)
    pos_idx = np.flatnonzero((pos_mask & foot).ravel())
    neg_cand = np.flatnonzero((foot & (d_cat > 3.0)).ravel())
    neg_idx = rng.choice(neg_cand, size=min(64000, neg_cand.size), replace=False)
    y = np.concatenate([np.ones(pos_idx.size), np.zeros(neg_idx.size)])
    out = {}
    for name, arr in (("trace_t_short_from_sphys", coh["t_short"]),
                      ("trace_t_long_from_sphys", coh["t_long"]),
                      ("trace_t_geo_from_sphys", coh["t_geo"]),
                      ("sphys_ch14_reference", s_phys)):
        flat = arr.ravel()
        v = np.concatenate([flat[pos_idx], flat[neg_idx]]).astype(np.float64)
        fin = np.isfinite(v)
        auc = float(roc_auc_score(y[fin], v[fin]))
        out[name] = {"auc_raw": round(auc, 5), "auc_oriented": round(max(auc, 1 - auc), 5)}
    worst = max(out.items(), key=lambda kv: kv[1]["auc_oriented"])
    res = {"n_pos_withheld_union": int(pos_idx.size), "n_neg_sampled": int(neg_idx.size),
           "tau": coh["tau"], "channels": out, "worst_channel": worst[0],
           "worst_auc_oriented": worst[1]["auc_oriented"], "threshold_auc": 0.90,
           "passed": bool(worst[1]["auc_oriented"] <= 0.90),
           "note": "Positives = union of withheld hide-and-recover pixels; negatives >3px from catalogue. Fields are label-free transforms of S_phys (UDSR channel 14)."}
    (ROOT / "evidence/trace_canary_20261028.json").write_text(json.dumps(res, indent=2) + "\n")
    log(f"[Canary] worst {worst[0]} oriented AUC={worst[1]['auc_oriented']} passed={res['passed']}")
    return res


def main() -> int:
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
        fold: binary_dilation(ctx.quad == fold, structure=np.ones((3, 3), bool),
                              iterations=holdout.COLLAR_PX) & foot
        for fold in holdout.FOLDS
    }

    canary = canary_trace_fields(ctx, s_phys_full, foot, d_cat_full)
    if not canary["passed"]:
        log("[STOP] leakage canary failed; no experiments run.")
        return 2

    # ---- baselines (controls only; not counted in the 3-experiment budget) ----
    eman = json.loads((ROOT / "registry/extended_registry_manifest.json").read_text())
    b2_entry = next(e for e in eman["rasters"] if e.get("sha256", "").startswith("c55bafc4"))
    b2_mask = holdout.read_binary(ROOT / b2_entry["local"])
    d28_mask = holdout.read_binary(ddir / "scored/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif")
    rep_b2_static = holdout.evaluate_hide_and_recover(b2_mask, ctx, b_visible_px=0.0, name="GEMSDOE32_B2_static")
    rep_b2_honest = holdout.evaluate_hide_and_recover(d28_mask, ctx, b_visible_px=2.0, name="D28_B2_fold_honest")
    sgmc_b2 = holdout.evaluate_sgmc_with_ci(b2_mask, ctx, name="GEMSDOE32_B2")
    log(f"[Baselines] B2 static={rep_b2_static['pooled_dti']:.6f} | D28_B2 fold-honest="
        f"{rep_b2_honest['pooled_dti']:.6f} | B2 SGMC_cal={sgmc_b2['sgmc_prevalence_calibrated_dti']:.6f}")

    # ---- per-cell hide-and-recover for the 3 experiments ----
    cells = {"EXP-1": {}, "EXP-2": {}, "EXP-3": {}}
    for idx_c, cell in enumerate(ctx.cells):
        tc = time.time()
        sl = cell.bbox
        elig_cell = cell.active_sub & (cell.d_visible_sub > B_PX)
        b_cell = int(round(BUDGET_FULL * int(elig_cell.sum()) / elig_full_count))
        elig_noplaya = elig_cell & ~flat_playa[sl]
        train_dom = foot & ~collars[cell.fold]
        m_full, m_gap, q_tab = udsr.fit_dual_cover_models(
            train_dom, cell.visible_full, lid_valid, base_mm, udsr_mm, seed=SEED + idx_c * 17)
        p_sub = udsr.predict_dual_cover_bbox(sl, elig_cell, lid_valid, base_mm, udsr_mm, m_full, m_gap, q_tab)
        del m_full, m_gap
        gc.collect()
        fld, _meta = fields_for(p_sub, elig_cell)
        cells["EXP-1"][cell.key] = emit_axial_crest_budget(fld["f1"], elig_noplaya, budget=b_cell, min_sep_px=MIN_SEP_PX)
        cells["EXP-2"][cell.key] = emit_axial_crest_budget(fld["f2"], elig_noplaya, budget=b_cell, min_sep_px=MIN_SEP_PX)
        f3 = exp3_field(fld["f2"], p_sub, elig_noplaya, budget=b_cell)
        cells["EXP-3"][cell.key] = emit_axial_crest_budget(f3, elig_noplaya, budget=b_cell, min_sep_px=MIN_SEP_PX)
        del fld, f3, p_sub
        gc.collect()
        log(f"  [Holdout {idx_c+1}/8 {cell.key}] b_cell={b_cell} done in {time.time()-tc:.1f}s "
            f"RSS={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024:.0f} MiB")

    hr = {
        "EXP-1": holdout.evaluate_hide_and_recover(cells["EXP-1"], ctx, b_visible_px=B_PX, name="EXP-1_CTRL-T0"),
        "EXP-2": holdout.evaluate_hide_and_recover(cells["EXP-2"], ctx, b_visible_px=B_PX, name="EXP-2_TRACE-T1"),
        "EXP-3": holdout.evaluate_hide_and_recover(cells["EXP-3"], ctx, b_visible_px=B_PX, name="EXP-3_TRACE-T2"),
    }
    for k, v in hr.items():
        log(f"[HR] {k} pooled HOLDOUT-DTI={v['pooled_dti']:.6f} CI={[round(x,5) for x in v['ci95_cluster_bootstrap']]}")
    del cells
    gc.collect()

    # ---- full-map 4-quadrant OOF posterior (for candidate rasters) ----
    log("[Full-Map OOF] stitching 4-quadrant collared Dual-Cover posterior...")
    p_full = np.zeros(foot.shape, dtype=np.float32)
    for fold in holdout.FOLDS:
        tf = time.time()
        q_mask = (ctx.quad == fold) & foot
        sl_q = ctx.quad_bboxes[fold]
        train_dom = foot & ~collars[fold]
        vis_train_only = ctx.labels & train_dom
        m_full, m_gap, q_tab = udsr.fit_dual_cover_models(
            train_dom, vis_train_only, lid_valid, base_mm, udsr_mm, seed=SEED + 500 + fold * 31)
        q_sub = q_mask[sl_q] & (d_cat_full[sl_q] > B_PX)
        pm_q = udsr.predict_dual_cover_bbox(sl_q, q_sub, lid_valid, base_mm, udsr_mm, m_full, m_gap, q_tab)
        p_full[sl_q] = np.where(q_mask[sl_q], pm_q, p_full[sl_q])
        del m_full, m_gap, pm_q
        gc.collect()
        log(f"  [Full-Map Fold {fold+1}/4] {time.time()-tf:.1f}s")

    elig_map = foot_noplaya & (d_cat_full > B_PX)
    fld, meta_full = fields_for(p_full, elig_map)
    f3_full = exp3_field(fld["f2"], p_full, elig_map, budget=BUDGET_FULL)
    raw_fields = {"EXP-1": fld["f1"], "EXP-2": fld["f2"], "EXP-3": f3_full}
    surfaces, masks = {}, {}
    for exp_id, raw in raw_fields.items():
        masks[exp_id] = emit_axial_crest_budget(raw, elig_map, budget=BUDGET_FULL, min_sep_px=MIN_SEP_PX)
        vmax = float(raw[elig_map].max()) if elig_map.any() else 1.0
        surfaces[exp_id] = np.where(elig_map, np.clip(raw / max(vmax, 1e-6), 0.0, 1.0), 0.0).astype(np.float32)
        log(f"[Full-Map {exp_id}] emitted {int(masks[exp_id].sum())} dots")
    np.savez(wdir / "trace_exp_checkpoint.npz",
             **{f"surf_{k}": surfaces[k] for k in surfaces},
             **{f"mask_{k}": masks[k].astype(np.uint8) for k in masks})

    # ---- SGMC diagnostic + registry audits per experiment ----
    entries = []
    for exp_id, title in (("EXP-1", "CTRL-T0"), ("EXP-2", "TRACE-T1"), ("EXP-3", "TRACE-T2")):
        ta = time.time()
        sg = holdout.evaluate_sgmc_with_ci(masks[exp_id], ctx, name=f"{exp_id}_{title}")
        aud_s = registry_audit.audit_surface(surfaces[exp_id], foot, eman, root=ROOT, template_tif=tpl_tif)
        aud_d = registry_audit.audit_final_dots(surfaces[exp_id], masks[exp_id], foot, eman,
                                                root=ROOT, template_tif=tpl_tif, space_filling_coverage=0.70)
        sparse = [r for r in aud_d["comparisons"]
                  if r.get("within_3px_fraction") is not None and not r.get("space_filling")]
        worst_sparse = max(sparse, key=lambda r: float(r["within_3px_fraction"])) if sparse else None
        entry = {
            "experiment_id": exp_id, "name": title,
            "holdout_hide_and_recover": strip_private(hr[exp_id]),
            "paired_vs_b2_fold_honest": paired_delta_from_boots(
                hr[exp_id]["pooled_dti"], hr[exp_id]["_boots"],
                rep_b2_honest["pooled_dti"], rep_b2_honest["_boots"]),
            "paired_vs_b2_static": paired_delta_from_boots(
                hr[exp_id]["pooled_dti"], hr[exp_id]["_boots"],
                rep_b2_static["pooled_dti"], rep_b2_static["_boots"]),
            "paired_vs_exp1_ctrl": paired_delta_from_boots(
                hr[exp_id]["pooled_dti"], hr[exp_id]["_boots"],
                hr["EXP-1"]["pooled_dti"], hr["EXP-1"]["_boots"]),
            "sgmc_diagnostic": strip_private(sg),
            "spatial_profile": spatial_profile(masks[exp_id], d_cat_full),
            "surface_audit": {"passed": aud_s["passed"], "audit_complete": aud_s["audit_complete"],
                              "registry_rasters": aud_s["registry_rasters"],
                              "worst_abs_spearman": round(float(aud_s["worst_abs_spearman"]), 6),
                              "worst_raster": aud_s["worst_raster"]},
            "dots_audit": {"passed_space_filling_calibrated": aud_d["passed"],
                           "literal_rule_passed": aud_d["literal_rule_passed"],
                           "audit_complete": aud_d["audit_complete"],
                           "registry_rasters": aud_d["registry_rasters"],
                           "candidate_dots": aud_d["candidate_dots"],
                           "worst_within_3px_fraction_literal": round(float(aud_d["worst_within_3px_fraction"]), 6),
                           "worst_literal_raster": aud_d["worst_overlap_raster"],
                           "worst_sparse_within_3px": round(float(worst_sparse["within_3px_fraction"]), 6) if worst_sparse else None,
                           "worst_sparse_raster": (f"{worst_sparse['repo']}:{worst_sparse['path']}" if worst_sparse else None)},
            "gate_G2_holdout": bool(hr[exp_id]["pooled_dti"] > CURRENT_BEST_HR),
        }
        entry["gate_G2_point_and_paired_ci"] = bool(
            entry["gate_G2_holdout"] and entry["paired_vs_b2_fold_honest"]["ci95_strictly_positive"])
        entries.append(entry)
        log(f"[{exp_id} {title}] {time.time()-ta:.1f}s HR={hr[exp_id]['pooled_dti']:.6f} "
            f"d_vs_B2h={entry['paired_vs_b2_fold_honest']['delta_dti']:+.6f} "
            f"SGMC_cal={sg['sgmc_prevalence_calibrated_dti']:.6f} "
            f"max|rho|={entry['surface_audit']['worst_abs_spearman']} "
            f"worst_sparse3px={entry['dots_audit']['worst_sparse_within_3px']} "
            f"literal_pass={entry['dots_audit']['literal_rule_passed']}")

    # ---- local prior-candidate overlaps (this repo's AP-1 / AP2 / H-UDSR) ----
    local = {}
    for name, fn in (("AP-1", "apartgemsdoe2-ap1-dilatcond-37654-20261027-1f26aa05-zeros.tif"),
                     ("AP2", "apartgemsdoe2-ap2-oofctrl-44090dots-20261027T220804Z-5e265df9-zeros.tif"),
                     ("H-UDSR-EXP3", "apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif")):
        m = holdout.read_binary(ROOT / "docs/downloads" / fn) & foot
        dm = distance_transform_edt(~m)
        local[name] = {eid: round(float((dm[masks[eid]] <= 3.0).mean()), 6) for eid in masks}
        local[name]["dots"] = int(m.sum())
    log(f"[Local overlaps] {local}")

    best_hr = max(entries, key=lambda e: e["holdout_hide_and_recover"]["pooled_dti"])
    summary = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.time() - t0, 2),
        "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1),
        "experiment_budget_used": 3, "experiment_budget_max": 3,
        "lane": "H-TRACE (knowledge/preregistration_trace_20261028.md)",
        "canary": canary,
        "baselines": {
            "GEMSDOE32_B2_static_holdout": strip_private(rep_b2_static),
            "D28_B2_fold_honest_holdout": strip_private(rep_b2_honest),
            "GEMSDOE32_B2_sgmc": strip_private(sgmc_b2),
            "archived_repo_best_hr_hudsr_exp2": CURRENT_BEST_HR,
        },
        "experiments": entries,
        "local_prior_candidate_overlap_within3px": local,
        "best_by_holdout": best_hr["experiment_id"],
        "fullmap_trace_tau": meta_full["tau"],
    }
    out = ROOT / "evidence/trace_three_experiments_20261028.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    log(f"[DONE] best={best_hr['experiment_id']} in {summary['elapsed_seconds']}s -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
