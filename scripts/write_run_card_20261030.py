#!/usr/bin/env python3
"""Write the run-card JSON for the 30 Oct 2026 candidates from their gate receipts (no hand-copied numbers).

Required fields (per the standing prompt, item 5): hypothesis, mechanism, named non-fault mimic,
holdout DTI + CI, registry correlation/overlap, raster SHA-256, validator output, unique name,
note <= 140 characters, verdict promote|negative. Unmeasured quantities are null.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CANDIDATES = [
    {
        "key": "catlogit-zeros",
        "gate": "evidence/gates_candidates_20261030_final.json",
        "lane": "H-CATLOGIT-OOF",
        "name": "ApartGEMS2 CATLOGIT-OOF 37654 (research, negative)",
        "note": "RESEARCH ONLY, NOT APPROVED. Quadrant-OOF catalogue logistic dots; below random null on SGMC proxy. Do not upload.",
        "hypothesis": "Catalogue-trained 19-band logistic discriminant, scored out-of-fold by quadrant, ranks unmapped fault-like ground.",
        "mechanism": "Leave-one-quadrant-out logistic regression on robust-standardised GeoDAWN/USGS/3DEP bands; catalogue cells masked; top 37,654 cells as binary dots.",
        "named_non_fault_mimic": "Alluvial-fan and pediment margins (steep relief and gravity gradients without slip).",
        "verdict": "negative",
        "preregistration": "knowledge/preregistration_catlogit_20261030.md",
    },
    {
        "key": "ieqtopn-zeros",
        "gate": "evidence/gates_candidates_20261030_final.json",
        "lane": "H-EQDENS-TOPN",
        "name": "ApartGEMS2 EQDENS-TOPN 37654 (research, negative)",
        "note": "RESEARCH ONLY, NOT APPROVED. Top 37654 cells by declustered earthquake intensity; below random null on SGMC proxy. Do not upload.",
        "hypothesis": "Declustered earthquake intensity (ieq_n100a15) marks active fault zones outside the catalogue.",
        "mechanism": "Single-band top-N ranking of non-catalogue footprint cells by ieq_n100a15 (rule fixed after the canary; SGMC not used for selection).",
        "named_non_fault_mimic": "Walker Lane seismic clusters around volcanic and hydrothermal centres with no mapped faults.",
        "verdict": "negative",
        "preregistration": "knowledge/preregistration_catlogit_20261030.md",
    },
]


def card(c: dict) -> dict:
    g = json.loads((ROOT / c["gate"]).read_text())
    k = c["key"]
    rec = g["candidates"][k]
    nan_key = k.replace("zeros", "nan")
    nan_rec = g["candidates"].get(nan_key, {})
    hr = rec["G2_proxies"]["HOLDOUT-DTI_hide_recover"]
    sg = rec["G2_proxies"]["SGMC-CAL_off_catalogue_proxy"]
    reg = rec["G3_registry"]
    null = rec["G2_random_null_same_n"]
    if len(c["note"]) > 140:
        raise SystemExit(f"note too long ({len(c['note'])}): {c['name']}")
    return {
        "schema": "apartgems-run-card-v3",
        "date_utc": datetime.now(timezone.utc).date().isoformat(),
        "lane": c["lane"],
        "name": c["name"],
        "note": c["note"],
        "note_chars": len(c["note"]),
        "hypothesis": c["hypothesis"],
        "mechanism": c["mechanism"],
        "named_non_fault_mimic": c["named_non_fault_mimic"],
        "experiment_index": {"catlogit-zeros": 1, "ieqtopn-zeros": 2}[k],
        "experiments_counted_total": 2,
        "weekly_slots_used": 0,
        "holdout_dti": {
            "HOLDOUT-DTI_hide_recover": {
                "score_label": "HOLDOUT-DTI", "evaluator_version": hr["evaluator_version"],
                "point": hr["pooled_dti"], "ci95": hr["ci95"], "withheld_positives": hr["n_withheld_positives"],
                "caveat": "Catalogue recovery; not the organizer target (masking) and has the split-geometry defect (issue #60).",
            },
            "SGMC_off_catalogue_proxy": {
                "score_label": "HOLDOUT-DTI (proxy)", "evaluator_version": sg["evaluator_version"],
                "raw_point": sg["raw_dti"], "raw_ci95": sg["raw_ci95"],
                "prevalence_calibrated_point": sg["prevalence_calibrated_dti"],
                "calibrated_ci95": sg["calibrated_ci95"], "truth_pixels": sg["n_truth_pixels"],
                "caveat": "Truth lies >300 m from the catalogue by construction, which penalises catalogue-adjacent placement.",
            },
            "random_null_same_n": {
                "seeds": null["seeds"], "SGMC_raw_values": null["SGMC_raw_dti_values"],
                "HR_values": null["HOLDOUT_hide_recover_values"],
            },
            "organizer_confirmed": None,
        },
        "registry_correlation_overlap": {
            "scope": "Focus registry (489 rasters, refreshed 30 Oct 2026) + 13GEMSDOE lattice; other listed repos NOT fetched.",
            "registry_rasters": reg["registry_rasters"],
            "malformed_or_missing": reg["malformed_or_missing"],
            "max_abs_spearman": reg["worst_abs_spearman"],
            "max_abs_spearman_raster": reg["worst_spearman_raster"],
            "literal_rule_passed": reg["literal_rule_passed"],
            "worst_within_3px": reg["worst_within_3px_fraction"],
            "worst_within_3px_raster": reg["worst_overlap_raster"],
            "worst_within_3px_excluding_space_filling": reg["worst_within_3px_excluding_space_filling"],
            "worst_within_3px_excluding_space_filling_raster": reg["worst_within_3px_excluding_space_filling_raster"],
            "literal_duplicates": reg["literal_duplicates"],
            "lattice_exemption": "none applied; lattice literal overlap is reported and fails",
        },
        "raster": {
            "zeros_outside": {"path": rec["file"], "sha256": rec["sha256"], "bytes": rec["bytes"]},
            "nan_outside": {"path": nan_rec.get("file"), "sha256": nan_rec.get("sha256"), "bytes": nan_rec.get("bytes")},
            "dots": rec["dots"],
        },
        "validator_output": {
            "tool": "gems32.submission.audit_geotiff (repo 12-point checker)",
            "all_checks_passed": rec["G1_format"]["all_checks_passed"],
            "checks": rec["G1_format"]["checks"],
            "in_footprint_min": rec["G1_format"]["in_footprint_min"],
            "in_footprint_max": rec["G1_format"]["in_footprint_max"],
            "on_catalogue_positive_pixels": rec["G1_format"]["on_catalogue_positive_pixels"],
            "organizer_template_authenticated": False,
            "portal_acceptance": None,
        },
        "verdict": c["verdict"],
        "verdict_reason": "Fails G2 (below matched random null on the off-catalogue proxy) and G3 literal rule (13GEMSDOE lattice); see gate receipt.",
        "preregistration": c["preregistration"],
        "gate_receipt": c["gate"],
    }


def main() -> int:
    out = {
        "schema": "apartgems-run-cards-v3",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "DO NOT SUBMIT. No candidate is approved; no selector run; no weekly slot used.",
        "cards": [card(c) for c in CANDIDATES],
    }
    (ROOT / "evidence" / "run_card_20261030.json").write_text(json.dumps(out, indent=2, default=float) + "\n")
    for c in out["cards"]:
        print(c["name"], len(c["note"]), c["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
