"""Local evidence selector for this repository; it never submits or selects a weekly slot.

This is not a modification or replacement of the pinned shared registry,
evaluator or release tools. It consumes their future verified receipts and
fails closed until provenance, complete literal comparisons, holdout and
saved-byte evidence are established. Shared issues are tracked upstream in
GEMSDOE32 #37, #41, #61, #63 and #67 and GEMSDOE24 #77.
"""
from __future__ import annotations

import math
import re

REQUIRED_VALIDATOR_CHECKS = (
    "geotiff", "single_band", "float32", "finite", "no_nan_inside_footprint",
    "no_nan_whole_raster", "no_masked_inside", "range_0_1", "crs_match",
    "shape_match", "transform_match", "outside_null_or_masked",
    "reference_self_contained", "candidate_self_contained",
    "nodata_none_zeros_outside", "zero_on_public_catalogue",
)


def _sha256(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _finite_between(value, low, high):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and low <= value <= high


def _holdout_valid(result):
    if not isinstance(result, dict):
        return False
    ci = result.get("ci95")
    return bool(
        isinstance(result.get("evaluator_version"), str) and result["evaluator_version"]
        and _sha256(result.get("evaluator_sha256"))
        and _sha256(result.get("fold_assignment_sha256"))
        and result.get("fold_local_visible_only") is True
        and result.get("zero_truth_fp_reconciled") is True
        and isinstance(result.get("n_withheld_positives"), int)
        and not isinstance(result.get("n_withheld_positives"), bool)
        and result["n_withheld_positives"] > 0
        and _finite_between(result.get("dti"), 0, 1)
        and isinstance(ci, (list, tuple)) and len(ci) == 2
        and all(_finite_between(v, 0, 1) for v in ci) and ci[0] <= ci[1]
    )


def _registry_receipt_valid(receipt, stage, manifest_sha, raster_sha=None):
    if not isinstance(receipt, dict):
        return False
    stages = {"surface": ("surface", "surface_before_placement"),
              "final": ("final", "final_dots")}
    base = (
        receipt.get("stage") in stages[stage]
        and receipt.get("passed") is True and receipt.get("audit_complete") is True
        and receipt.get("registry_files_hash_verified") is True
        and receipt.get("registry_snapshot_sha256") == manifest_sha
        and isinstance(receipt.get("registry_rasters"), int)
        and not isinstance(receipt.get("registry_rasters"), bool)
        and receipt["registry_rasters"] > 0
        and receipt.get("malformed_or_missing") == 0
        and receipt.get("constant_or_empty") == 0
        and _finite_between(receipt.get("worst_abs_spearman"), 0, 0.90)
    )
    if stage == "final":
        base = (base and receipt.get("literal_rule_passed") is True
                and receipt.get("rank_basis") == "saved_final_dots"
                and _finite_between(receipt.get("worst_within_3px_fraction"), 0, 0.70)
                and _sha256(raster_sha) and receipt.get("candidate_raster_sha256") == raster_sha)
    return bool(base)


def promotion_decision(*, lane, surface_check, final_check, canary_aucs,
                       holdout, incumbent, same_evaluation, validator,
                       paired_delta_ci95=None, preflight=None, tested_feature_ids=None):
    """Select a candidate for further consideration, never a competition slot.

    ``preflight`` must be the automated current-session result. Missing or
    unsupported evidence is negative. Matching evaluator and fold hashes,
    reconciled zero-truth FP mass, complete literal novelty receipts, every
    named feature canary, authenticated reference and read-back SHA are required.
    """
    issues = []
    auth = preflight if isinstance(preflight, dict) else {}
    if not (isinstance(lane, str) and lane.strip()
            and auth.get("status") == "READY"
            and auth.get("new_experiment_authorized") is True
            and auth.get("lane_assigned") is True
            and auth.get("assigned_lane") == lane
            and auth.get("complete_parallel_registry") is True
            and auth.get("template_origin_authenticated") is True):
        issues.append("current automated preflight does not authorize this assigned lane")

    manifest_sha = auth.get("registry_snapshot_sha256")
    raster_sha = validator.get("raster_sha256") if isinstance(validator, dict) else None
    if not _sha256(manifest_sha):
        issues.append("complete registry snapshot hash is missing")
    if not _registry_receipt_valid(surface_check, "surface", manifest_sha):
        issues.append("pre-placement surface audit is missing, incomplete or failed")
    if not _registry_receipt_valid(final_check, "final", manifest_sha, raster_sha):
        issues.append("final literal dot audit is missing, incomplete, unbound or failed")
    if (isinstance(surface_check, dict) and isinstance(final_check, dict)
            and surface_check.get("registry_rasters") != final_check.get("registry_rasters")):
        issues.append("surface and final audits cover different registry counts")

    expected = auth.get("expected_feature_ids")
    ids = tested_feature_ids
    if not (isinstance(expected, list) and expected and all(isinstance(v, str) and v for v in expected)
            and len(set(expected)) == len(expected) and isinstance(ids, list)
            and all(isinstance(v, str) and v for v in ids)
            and len(ids) == len(expected) and len(set(ids)) == len(ids)
            and set(ids) == set(expected) and isinstance(canary_aucs, (list, tuple))
            and len(canary_aucs) == len(ids)
            and all(_finite_between(v, 0, 1) and max(v, 1-v) <= 0.90 for v in canary_aucs)):
        issues.append("each named feature needs a passing oriented leakage canary")

    if not (_holdout_valid(holdout) and _holdout_valid(incumbent)):
        issues.append("holdout records or fold-local provenance are missing or invalid")
    else:
        comparable = (same_evaluation is True
                      and holdout["evaluator_version"] == incumbent["evaluator_version"]
                      and holdout["evaluator_sha256"] == incumbent["evaluator_sha256"]
                      and holdout["fold_assignment_sha256"] == incumbent["fold_assignment_sha256"]
                      and holdout["n_withheld_positives"] == incumbent["n_withheld_positives"])
        if not comparable:
            issues.append("candidate and incumbent are not on the same verified evaluator and folds")
        elif holdout["dti"] <= incumbent["dti"]:
            issues.append("candidate does not beat incumbent")
    if not (isinstance(paired_delta_ci95, (tuple, list)) and len(paired_delta_ci95) == 2
            and all(_finite_between(v, -1, 1) for v in paired_delta_ci95)
            and 0 < paired_delta_ci95[0] <= paired_delta_ci95[1]):
        issues.append("paired improvement interval is missing, invalid or not strictly positive")
    if not (isinstance(validator, dict) and _sha256(raster_sha)
            and all(validator.get(k) is True for k in REQUIRED_VALIDATOR_CHECKS)):
        issues.append("saved-byte validator or reference checks are incomplete")
    return {"verdict": "negative" if issues else "promote", "issues": issues,
            "slot_approved": False,
            "slot_note": "A separate weekly-slot selector is required; this function never submits."}
