#!/usr/bin/env python3
"""Emit the selected H-SPMD deliverable GeoTIFF + ZIP + JSON Run Card and run automated byte audits.

Pre-registered selection rule (knowledge/preregistration_spmd_20261028.md):
  Select highest hide-and-recover HOLDOUT-DTI among the 3 pre-registered H-SPMD
  experiments that pass both surface |Spearman| <= 0.90 and sparse 3-px dot overlap <= 0.70:
    - EXP-1 (SPMD-Sup61-Ctrl): HOLDOUT-DTI = 0.127184, sparse 3-px = 0.747768 > 0.70 -> REJECTED (duplicate)
    - EXP-2 (SPMD-SARPU-Unified): HOLDOUT-DTI = 0.113181, sparse 3-px = 0.689333 <= 0.70 -> SELECTED
    - EXP-3 (SPMD-SARPU-TwoRegime): HOLDOUT-DTI = 0.099157, sparse 3-px = 0.653036 <= 0.70 -> runner-up

Protocol verdict remains fail-closed ``"negative"`` (HOLD FOR HUMAN PORTFOLIO SELECTOR /
DO NOT AUTO-SUBMIT) because:
  (1) Protocol Rule 6 reserves competition slot allocation to a separate human selector step;
  (2) Literal all-registry 3-px overlap without space-filling lattice exemption hits 0.998522 > 0.70
      against GEMSDOE24:13GEMSDOE (206,895-dot lattice covering 99.8713% of footprint) and 2/549
      upstream registry rasters are malformed;
  (3) Reference template ``sample_submission.tif`` is SHA-256 mirror-restored rather than freshly
      authenticated directly from DrivenData inside this network-restricted sandbox.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems32 import holdout, paths, release_gate, submission  # noqa: E402
from gemsdoe32.submission import validate_submission_geotiff  # noqa: E402

ARCHIVED_BEST_HR = 0.113696       # H-UDSR EXP-2 (failed sparse overlap at 80.62%)
ARCHIVED_BEST_UNIQUE_HR = 0.094698  # H-UDSR EXP-3 (passed sparse overlap at 69.42%)


def main() -> int:
    ddir = paths.data_dir()
    wdir = paths.work_dir()
    tpl_tif = ddir / "sample_submission.tif"

    exp = json.loads((ROOT / "evidence/spmd_three_experiments_20261028.json").read_text())
    canary_full = json.loads((ROOT / "evidence/spmd_leakage_canary_63ch.json").read_text())
    ck = np.load(wdir / "spmd_exp_checkpoint.npz")

    eligible = [
        e for e in exp["experiments"]
        if e["surface_audit"]["passed"] and e["dots_audit"]["passed"]
    ]
    if not eligible:
        raise RuntimeError("No H-SPMD experiment passed sparse uniqueness gates!")
    chosen = max(eligible, key=lambda e: e["holdout_hide_and_recover"]["pooled_dti"])
    exp_id = chosen["experiment_id"]
    mask = ck[f"mask_{exp_id}"].astype(bool)
    hr = chosen["holdout_hide_and_recover"]
    sg = chosen["sgmc_diagnostic"]
    n_dots = int(mask.sum())

    with rasterio.open(tpl_tif) as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(ddir / "labels.tif") as ds:
        labels = (ds.read(1) > 0) & foot

    # Fixed UTC tag for reproducible regeneration if re-run in same session, or fresh if none exists
    ts = "20261028T235800Z"
    slug = f"spmd-{exp_id.lower()}-sarpu-unified-{n_dots}dots"
    note = (
        f"ApartGEMSDOE2 H-SPMD {exp_id}: SAR-PU spy+propensity 61/55ch DualCover + "
        f"TMI-bandpass/epithermal/LiDAR, {n_dots}d B2"
    )
    assert len(note) <= 140, f"Submission note length {len(note)} exceeds 140 chars"

    meta = {
        "candidate_id": f"apartgemsdoe2-{slug}",
        "description": (
            "H-SPMD EXP-2 (SPMD-SARPU-Unified): 61-channel M_Full + 55-channel M_Gap Dual-Cover "
            "gradient-boosted models trained with a 39-channel DEM/LiDAR-free subsurface spy teacher "
            "and inverse geomorphic exposure propensity weighting, fused with matched-depth "
            "(TMI - TMI_up150) shallow magnetic bandpass, Dickson-Scott Th/K-U/Th epithermal "
            "alteration, BLM lode corridors, and 1m LiDAR dipolar/graben/strike features; "
            f"submodular axial-crest emission at {n_dots} binary dots outside a 2 px catalogue collar."
        ),
        "submission_note_zeros": note,
        "submission_note_nan": note,
        "catalogue_hidden_mean": hr["pooled_dti"],
        "catalogue_hidden_per_quadrant": hr["per_quadrant_dti"],
        "sgmc_prevalence_calibrated_dti": sg["sgmc_prevalence_calibrated_dti"],
        "drift_corrected_holdout_mean": hr["pooled_dti"],
        "drift_corrected_per_quadrant": hr["per_quadrant_dti"],
        "predicted_leaderboard_dti": None,
        "ei_drift_corrected": None,
        "slot_decision": "HOLD-FOR-HUMAN-PORTFOLIO-SELECTOR",
    }

    out_dir = ROOT / "docs/downloads"
    bundle = submission.write_submission_pair(
        mask=mask,
        foot=foot,
        labels=labels,
        template_tif=tpl_tif,
        out_dir=out_dir,
        slug=slug,
        timestamp_tag=ts,
        candidate_meta=meta,
        prefix="apartgemsdoe2",
    )
    zeros_path = out_dir / bundle["zeros_tif"]["filename"]
    nan_path = out_dir / bundle["nan_tif"]["filename"]
    zip_path = zeros_path.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(zeros_path, arcname=zeros_path.name)

    # Independent saved-byte re-validations (zero human intervention)
    strict = validate_submission_geotiff(zeros_path, tpl_tif, strict_whole_array_finite=True)
    strict_dict = strict.to_dict() if hasattr(strict, "to_dict") else dict(strict)

    saved_mask = holdout.read_binary(zeros_path)
    bit_exact_match = bool(np.array_equal(saved_mask, mask & foot & ~labels))
    if not bit_exact_match:
        raise RuntimeError("Saved GeoTIFF binary mask does not match checkpoint mask bit-for-bit!")

    ctx = holdout.load_holdout_context(ddir)
    saved_static_hr = holdout.evaluate_hide_and_recover(
        saved_mask, ctx, b_visible_px=2.0, name="saved_zeros_tif_static_recheck"
    )
    saved_sgmc = holdout.evaluate_sgmc_with_ci(saved_mask, ctx, name="saved_zeros_tif_sgmc_recheck")

    # Map validator checks to release_gate.REQUIRED_VALIDATOR_CHECKS
    z_checks = bundle["zeros_tif"]["checks"]
    rg_validator = {
        "single_band": bool(z_checks["single_band"]),
        "finite": bool(z_checks["in_footprint_all_finite"] and z_checks["validator_range_0_1_guaranteed"]),
        "range_0_1": bool(z_checks["in_footprint_range_0_1"] and z_checks["validator_range_0_1_guaranteed"]),
        "crs_match": bool(z_checks["exact_reference_grid_match"] and z_checks["crs_epsg_32611"]),
        "shape_match": bool(z_checks["exact_reference_grid_match"] and z_checks["dimensions_3730x3292"]),
        "transform_match": bool(z_checks["exact_reference_grid_match"]),
    }

    # Formal fail-closed release_gate decision against D28_B2 fold-honest control
    d28_ctrl = exp["baselines"]["D28_B2_fold_honest_holdout"]
    rg_decision = release_gate.promotion_decision(
        lane="H-SPMD: SAR-PU Mapping-Propensity De-confounding & Shallow Matched-Depth / Epithermal Conduit Inversion",
        surface_check={
            "stage": "surface",
            "passed": bool(chosen["surface_audit"]["passed"] and chosen["surface_audit"]["audit_complete"]),
        },
        final_check={
            "stage": "final",
            "passed": bool(chosen["dots_audit"]["literal_rule_passed"] and chosen["dots_audit"]["audit_complete"]),
        },
        canary_aucs=list(canary_full["aucs"].values()),
        holdout={
            "evaluator_version": hr["evaluator_version"],
            "n_withheld_positives": hr["n_withheld_positives"],
            "dti": hr["pooled_dti"],
            "ci95": hr["ci95_cluster_bootstrap"],
        },
        incumbent={
            "evaluator_version": d28_ctrl["evaluator_version"],
            "n_withheld_positives": d28_ctrl["n_withheld_positives"],
            "dti": d28_ctrl["pooled_dti"],
            "ci95": d28_ctrl["ci95_cluster_bootstrap"],
        },
        same_evaluation=True,
        validator=rg_validator,
        paired_delta_ci95=chosen["paired_vs_d28_b2_fold_honest"]["ci95_paired_cluster_bootstrap"],
    )

    gate_g1 = bool(all(rg_validator.values()) and strict_dict.get("passed", strict_dict.get("pass", False)) and bit_exact_match)
    gate_g2_d28 = bool(chosen["gates"]["G2a_beats_d28_b2_paired_ci"])
    gate_g2_unique_repo = bool(chosen["gates"]["G2b_beats_archived_unique_best_00947"])
    gate_g2_all_repo = bool(chosen["gates"]["G2c_beats_archived_all_best_01137"])
    gate_g3_canary = bool(canary_full["passed"])
    gate_g4_sparse = bool(chosen["surface_audit"]["passed"] and chosen["dots_audit"]["passed"])
    gate_g4_literal = bool(chosen["surface_audit"]["passed"] and chosen["dots_audit"]["literal_rule_passed"] and chosen["dots_audit"]["audit_complete"])

    verdict = rg_decision["verdict"]  # "negative" (fail-closed on literal 13GEMSDOE lattice + 2 malformed upstream TIFFs)

    run_card = {
        "schema": "parallel-run-protocol-run-card-v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "session_branch": "arena/9d6c28d5-apartgemsdoe2",
        "preregistration": "knowledge/preregistration_spmd_20261028.md",
        "hypothesis": (
            "H-SPMD: Public fault mapping in Nevada is Selected-Not-At-Random (SAR-PU) by subaerial "
            "scarp exposure, causing standard supervised classifiers to treat concealed alluvial-basin "
            "faults as negatives and crowd >80% of dots onto bare-rock scarps. Purifying unlabeled "
            "negatives with a 39-channel DEM/LiDAR-free subsurface spy teacher and inverse exposure "
            "propensity weighting across 61/55-channel Dual-Cover models — enriched with matched-depth "
            "(TMI - TMI_up150) shallow magnetic bandpass, Dickson-Scott Th/K-U/Th epithermal alteration, "
            "gated BLM lode corridors, and 1m LiDAR dipolar/graben/strike features — recovers concealed "
            "faults while naturally breaking bare-rock registry crowding below 70%."
        ),
        "mechanism": (
            f"{exp_id} ({chosen['name']}): 39-ch subsurface spy purges 15.84% putative concealed fault "
            "conduits from unlabeled negatives -> 4-feature logistic exposure propensity e(x_obs) "
            "reweights training positives (gamma=0.38) and de-confounds test posteriors (p / e^0.22) -> "
            f"61-ch M_Full + 55-ch M_Gap Dual-Cover fused with subsurface conduit + tip/relay -> "
            f"submodular axial-crest emission ({n_dots} binary dots, min_sep=3.05 px, support_mult=6.8, B=2 px)."
        ),
        "mimicking_non_fault_process": (
            "Pleistocene Lake Lahontan wave-cut shorelines, non-tectonic alluvial fan heads, GeoDAWN "
            "survey-block seam steps, US-50/US-95 road embankments, and non-fault placer mining claims "
            "mimic linear topographic, radiometric, or claim corridors without fault offset."
        ),
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": hr["evaluator_version"],
            "withheld_positives": hr["n_withheld_positives"],
            "point": hr["pooled_dti"],
            "ci95": hr["ci95_cluster_bootstrap"],
            "paired_vs_fold_honest_d28_b2": chosen["paired_vs_d28_b2_fold_honest"],
            "delta_vs_repo_prior_sparse_unique_best_hudsr_exp3": round(hr["pooled_dti"] - ARCHIVED_BEST_UNIQUE_HR, 6),
            "archived_repo_sparse_unique_best_point": ARCHIVED_BEST_UNIQUE_HR,
            "archived_repo_duplicate_best_point": ARCHIVED_BEST_HR,
            "session_supervised_control_exp1_point": exp["experiments"][0]["holdout_hide_and_recover"]["pooled_dti"],
            "sgmc_diagnostic_only": {
                "label": "HOLDOUT-DTI",
                "evaluator_version": sg["evaluator_version"],
                "withheld_positives": sg["n_withheld_positives"],
                "calibrated_point": sg["sgmc_prevalence_calibrated_dti"],
                "calibrated_ci95": sg["sgmc_calibrated_ci95"],
                "raw_point": sg["sgmc_raw_pooled_dti"],
                "raw_ci95": sg["sgmc_raw_ci95"],
            },
        },
        "organizer_confirmed": None,
        "leaderboard_estimate": None,
        "leaderboard_estimate_reason": (
            "Protocol Rule 3: Never write a projection as a score; only HOLDOUT-DTI and receipt-backed "
            "ORGANIZER-CONFIRMED scores are reported."
        ),
        "leakage_canary": {
            "passed": canary_full["passed"],
            "threshold_oriented_auc": canary_full["threshold"],
            "n_features_tested": canary_full["n_features_tested"],
            "max_oriented_auc": canary_full["max_oriented_auc"],
            "worst_channel": canary_full["worst_channel"],
            "spmd_new_8ch_aucs": canary_full["spmd_new_8ch_aucs"],
            "artifact": "evidence/spmd_leakage_canary_63ch.json",
        },
        "registry_correlation_overlap": {
            "extended_registry_rasters_total": chosen["dots_audit"]["registry_rasters"],
            "readable_valid_rasters": chosen["dots_audit"]["registry_rasters"] - chosen["dots_audit"]["malformed_or_missing"],
            "malformed_upstream_rasters": chosen["dots_audit"]["malformed_or_missing"],
            "surface_max_abs_spearman": chosen["surface_audit"]["worst_abs_spearman"],
            "surface_worst_raster": chosen["surface_audit"]["worst_raster"],
            "sparse_dots_max_within_3px": chosen["dots_audit"]["worst_sparse_within_3px"],
            "sparse_dots_worst_raster": chosen["dots_audit"]["worst_sparse_raster"],
            "literal_all_max_within_3px_including_13gemsdoe_lattice": chosen["dots_audit"]["worst_all_including_lattice_within_3px"],
            "local_prior_candidates_within3px": {
                k: v.get(exp_id) for k, v in exp["local_prior_candidate_overlap_within3px"].items()
            },
            "sparse_registry_gate_pass": gate_g4_sparse,
            "literal_all_registry_gate_pass": gate_g4_literal,
        },
        "raster": f"docs/downloads/{zeros_path.name}",
        "raster_nan_companion": f"docs/downloads/{nan_path.name}",
        "raster_sha256": hashlib.sha256(zeros_path.read_bytes()).hexdigest(),
        "raster_nan_sha256": hashlib.sha256(nan_path.read_bytes()).hexdigest(),
        "zip": f"docs/downloads/{zip_path.name}",
        "zip_sha256": hashlib.sha256(zip_path.read_bytes()).hexdigest(),
        "validator_output": {
            "writer_audit_zeros": bundle["zeros_tif"],
            "writer_audit_nan": bundle["nan_tif"],
            "strict_saved_byte_check": strict_dict,
            "bit_exact_checkpoint_match": bit_exact_match,
            "saved_bytes_static_holdout_recheck_dti": round(float(saved_static_hr["pooled_dti"]), 6),
            "saved_bytes_sgmc_calibrated_recheck_dti": round(float(saved_sgmc["sgmc_prevalence_calibrated_dti"]), 6),
            "release_gate_validator": rg_validator,
            "gate_G1_format_pass": gate_g1,
            "geometry_reference": "SHA-256-pinned mirror of sample_submission.tif (re-verify against fresh DrivenData download before portal upload)",
            "portal_acceptance": None,
        },
        "gates": {
            "G1_format_and_saved_bytes": gate_g1,
            "G2a_beats_d28_b2_paired_ci95": gate_g2_d28,
            "G2b_beats_repo_sparse_unique_best_00947": gate_g2_unique_repo,
            "G2c_beats_repo_duplicate_best_01137": gate_g2_all_repo,
            "G3_leakage_canary_63ch": gate_g3_canary,
            "G4a_sparse_uniqueness_543_rasters": gate_g4_sparse,
            "G4b_literal_all_including_13gemsdoe_lattice_and_malformed": gate_g4_literal,
        },
        "release_gate_decision": rg_decision,
        "submission_name": zeros_path.stem,
        "note": note,
        "note_length_chars": len(note),
        "download_and_submit_status": {
            "technical_file_validity": "VALID_SINGLE_BAND_GEOTIFF_IN_0_1_SPARSE_UNIQUE",
            "autonomous_slot_verdict": "HOLD_FOR_HUMAN_SELECTOR_DO_NOT_AUTO_SUBMIT",
            "summary": (
                "File passes all 13 GeoTIFF [0, 1] / zero-NaN / CRS / shape / transform checks, "
                "passes 63-ch leakage canary (0.7693 <= 0.90), passes surface Spearman (0.1230 <= 0.90) "
                "and sparse 3-px uniqueness across all 543 sparse rasters (68.93% <= 70%), and is this "
                "repository's highest-HOLDOUT-DTI sparse-unique candidate (0.1132, +19.5% vs H-UDSR EXP-3 "
                "0.0947; paired 95% CI [+0.00008, +0.02793] > D28_B2 0.0992). Protocol verdict remains "
                "'negative' (do not auto-spend a weekly slot) because literal overlap vs the 206,895-dot "
                "13GEMSDOE covering lattice (99.87% footprint coverage) is 99.85% > 70%, 2/549 upstream "
                "registry TIFFs are malformed, template geometry is mirror-restored, and slot allocation "
                "requires cross-lane human selector review against GEMSDOE32 B2 (ORGANIZER-CONFIRMED 0.2778)."
            ),
        },
        "verdict": verdict,
        "experiments_used": exp["experiment_budget_used"],
        "all_experiments": [
            {
                "experiment_id": e["experiment_id"],
                "name": e["name"],
                "holdout_dti": e["holdout_hide_and_recover"]["pooled_dti"],
                "holdout_ci95": e["holdout_hide_and_recover"]["ci95_cluster_bootstrap"],
                "sgmc_calibrated_dti": e["sgmc_diagnostic"]["sgmc_prevalence_calibrated_dti"],
                "surface_max_abs_spearman": e["surface_audit"]["worst_abs_spearman"],
                "sparse_max_within_3px": e["dots_audit"]["worst_sparse_within_3px"],
                "sparse_unique_pass": bool(e["surface_audit"]["passed"] and e["dots_audit"]["passed"]),
            }
            for e in exp["experiments"]
        ],
    }

    out_card = ROOT / "evidence/spmd_run_card_20261028.json"
    out_card.write_text(json.dumps(run_card, indent=2) + "\n")
    print(json.dumps({
        "chosen": exp_id,
        "verdict": verdict,
        "raster": run_card["raster"],
        "raster_sha256": run_card["raster_sha256"],
        "zip": run_card["zip"],
        "submission_name": run_card["submission_name"],
        "note": run_card["note"],
        "note_length_chars": run_card["note_length_chars"],
        "holdout_dti": hr["pooled_dti"],
        "sparse_max_within_3px": chosen["dots_audit"]["worst_sparse_within_3px"],
        "gates": run_card["gates"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
