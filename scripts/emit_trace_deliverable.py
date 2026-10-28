#!/usr/bin/env python3
"""Emit the selected H-TRACE candidate GeoTIFF + ZIP and its JSON run card.

Selection (pre-registered): highest hide-and-recover HOLDOUT-DTI among the three
experiments that pass the surface-Spearman and sparse final-dot uniqueness gates.
Verdict ``promote`` requires ALL gates G1-G4 including the literal lattice rule;
otherwise the file is written as a clearly-labelled RESEARCH artifact with
verdict ``negative``.  Uses the shared writer (``gems32.submission``) with this
repo's prefix; never deletes other downloads; never submits anything.
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

from gems32 import paths, submission  # noqa: E402
from gemsdoe32.submission import validate_submission_geotiff  # noqa: E402

CURRENT_BEST_HR = 0.113696


def main() -> int:
    ddir = paths.data_dir()
    wdir = paths.work_dir()
    tpl_tif = ddir / "sample_submission.tif"
    exp = json.loads((ROOT / "evidence/trace_three_experiments_20261028.json").read_text())
    ck = np.load(wdir / "trace_exp_checkpoint.npz")

    def sparse_ok(e: dict) -> bool:
        return bool(e["surface_audit"]["passed"] and e["dots_audit"]["passed_space_filling_calibrated"])

    eligible = [e for e in exp["experiments"] if sparse_ok(e)]
    if eligible:
        chosen = max(eligible, key=lambda e: e["holdout_hide_and_recover"]["pooled_dti"])
        selection_basis = "best HOLDOUT-DTI among sparse-uniqueness-passing experiments"
    else:
        chosen = next(e for e in exp["experiments"] if e["experiment_id"] == "EXP-2")
        selection_basis = ("no experiment passed the sparse-uniqueness gate; EXP-2 TRACE-T1 emitted "
                           "as the direct lane realization (research only). EXP-1 CTRL scored higher "
                           "on hide-and-recover but is the comparator, not the lane.")
    exp_id = chosen["experiment_id"]
    mask = ck[f"mask_{exp_id}"].astype(bool)
    hr = chosen["holdout_hide_and_recover"]
    sg = chosen["sgmc_diagnostic"]
    n_dots = int(mask.sum())

    gate_g2 = bool(chosen["gate_G2_point_and_paired_ci"])
    gate_g4_sparse = sparse_ok(chosen)
    gate_g4_literal = bool(chosen["surface_audit"]["passed"] and chosen["dots_audit"]["literal_rule_passed"])
    canary_ok = bool(exp["canary"]["passed"])

    with rasterio.open(tpl_tif) as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(ddir / "labels.tif") as ds:
        labels = (ds.read(1) > 0) & foot

    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    slug = f"trace-{exp_id.lower()}-{chosen['name'].lower()}-{n_dots}dots"
    note = (f"ApartGEMSDOE2 H-TRACE {exp_id}: oriented 1.5/3.1km trace-coherence gate on "
            f"DualCover OOF posterior, {n_dots} dots B2")
    assert len(note) <= 140, len(note)
    meta = {
        "candidate_id": f"apartgemsdoe2-{slug}",
        "description": ("H-TRACE oriented line-integral trace-coherence (1.5 km + 3.1 km, 8 orientations) "
                        "applied to the leak-free H-UDSR Dual-Cover OOF posterior; shared exact-gain "
                        "axial-crest emission at 37,654-dot budget outside a 2 px catalogue collar."),
        "submission_note_zeros": note,
        "submission_note_nan": note,
        "catalogue_hidden_mean": hr["pooled_dti"],
        "catalogue_hidden_per_quadrant": hr["per_quadrant_dti"],
        "sgmc_prevalence_calibrated_dti": sg["sgmc_prevalence_calibrated_dti"],
        "drift_corrected_holdout_mean": hr["pooled_dti"],
        "drift_corrected_per_quadrant": hr["per_quadrant_dti"],
        "predicted_leaderboard_dti": None,
        "ei_drift_corrected": None,
        "slot_decision": "RESEARCH-ONLY-PENDING-SELECTOR",
    }
    out_dir = ROOT / "docs/downloads"
    bundle = submission.write_submission_pair(
        mask=mask, foot=foot, labels=labels, template_tif=tpl_tif, out_dir=out_dir,
        slug=slug, timestamp_tag=ts, candidate_meta=meta, prefix="apartgemsdoe2")
    zeros_path = out_dir / bundle["zeros_tif"]["filename"]
    zip_path = zeros_path.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(zeros_path, arcname=zeros_path.name)

    # Independent saved-byte re-validation (strict whole-array finite [0,1]).
    strict = validate_submission_geotiff(zeros_path, tpl_tif, strict_whole_array_finite=True)
    strict_dict = strict.to_dict() if hasattr(strict, "to_dict") else dict(strict)
    gate_g1 = bool(strict_dict.get("passed", strict_dict.get("pass", False)))

    verdict = "promote" if (gate_g1 and gate_g2 and canary_ok and gate_g4_literal) else "negative"
    run_card = {
        "schema": "parallel-run-protocol-run-card-v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "session_branch": "arena/7ec4400f-apartgemsdoe2",
        "preregistration": "knowledge/preregistration_trace_20261028.md",
        "hypothesis": ("H-TRACE: km-scale oriented trace coherence of the leak-free Dual-Cover OOF "
                       "posterior separates genuine fault traces (sustained collinear support over "
                       "1.5-3.1 km) from pixelwise posterior speckle, raising kernel credit per dot "
                       "on expert-hidden faults missing from the USGS/INGENIOUS catalogue."),
        "mechanism": (f"{exp_id} {chosen['name']}: dual-cover OOF posterior -> two-scale oriented "
                      "line-integral coherence gate -> shared axial-crest exact-gain emission, "
                      f"{n_dots} binary dots, min-sep 2.9 px, B=2 px catalogue collar."),
        "named_non_fault_mimic": ("Roads/rail embankments, Pleistocene Lake Lahontan shoreline benches, "
                                  "and GeoDAWN flight-line stripes are long linear features that also "
                                  "produce oriented coherence without faulting."),
        "holdout_dti": {
            "label": "HOLDOUT-DTI", "evaluator_version": hr["evaluator_version"],
            "withheld_positives": hr["n_withheld_positives"], "point": hr["pooled_dti"],
            "ci95": hr["ci95_cluster_bootstrap"],
            "paired_vs_fold_honest_d28_b2": chosen["paired_vs_b2_fold_honest"],
            "archived_repo_best_point": CURRENT_BEST_HR,
            "sgmc_diagnostic_only": {"evaluator_version": sg["evaluator_version"],
                                     "withheld_positives": sg["n_withheld_positives"],
                                     "calibrated_point": sg["sgmc_prevalence_calibrated_dti"],
                                     "calibrated_ci95": sg["sgmc_calibrated_ci95"]},
        },
        "organizer_confirmed": None,
        "leaderboard_estimate": None,
        "leaderboard_estimate_reason": ("No calibrated mapping from catalogue hide-and-recover to the "
                                        "expert-hidden test set exists; a projection is never a score."),
        "leakage_canary": exp["canary"],
        "registry_correlation_overlap": {
            "surface": chosen["surface_audit"], "dots": chosen["dots_audit"],
            "local_prior_candidates_within3px": {
                k: v.get(exp_id) for k, v in exp["local_prior_candidate_overlap_within3px"].items()},
            "literal_all_registry_gate_pass": gate_g4_literal,
            "sparse_registry_gate_pass": gate_g4_sparse,
        },
        "raster": f"docs/downloads/{zeros_path.name}",
        "raster_sha256": hashlib.sha256(zeros_path.read_bytes()).hexdigest(),
        "zip": f"docs/downloads/{zip_path.name}",
        "validator_output": {
            "writer_audit_zeros": bundle["zeros_tif"], "writer_audit_nan": bundle["nan_tif"],
            "strict_saved_byte_check": strict_dict, "gate_G1_format_pass": gate_g1,
            "reference": "owner-mirrored sample_submission.tif (not organizer-authenticated)",
            "portal_acceptance": None,
        },
        "gates": {"G1_format": gate_g1, "G2_holdout_point_and_paired_ci": gate_g2,
                  "G3_canary": canary_ok, "G4_sparse_uniqueness": gate_g4_sparse,
                  "G4_literal_including_space_filling_lattice": gate_g4_literal},
        "submission_name": zeros_path.stem,
        "note": note, "note_length_chars": len(note),
        "verdict": verdict,
        "experiments_used": exp["experiment_budget_used"],
        "all_experiments": [
            {"experiment_id": e["experiment_id"], "name": e["name"],
             "holdout_dti": e["holdout_hide_and_recover"]["pooled_dti"],
             "holdout_ci95": e["holdout_hide_and_recover"]["ci95_cluster_bootstrap"],
             "sgmc_cal": e["sgmc_diagnostic"]["sgmc_prevalence_calibrated_dti"]}
            for e in exp["experiments"]],
    }
    out_card = ROOT / "evidence/trace_run_card_20261028.json"
    out_card.write_text(json.dumps(run_card, indent=2) + "\n")
    print(json.dumps({"chosen": exp_id, "verdict": verdict, "raster": run_card["raster"],
                      "sha256": run_card["raster_sha256"], "gates": run_card["gates"],
                      "holdout_dti": hr["pooled_dti"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
