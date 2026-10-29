#!/usr/bin/env python3
"""Fail-closed current-run preflight; it never trains, writes TIFFs or selects slots."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from datetime import datetime, timezone

from audit_historical import ROOT, sha256_file


def inspect_core_data(manifest: dict, data_root: Path) -> list[dict]:
    """Check current bytes, not the historical restore receipt.

    Hash agreement verifies the pinned mirror only, not organizer provenance.
    """
    results = []
    for item in manifest["files"]:
        if item["group"] != "core":
            continue
        relative = Path(item["dest"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe core-data path")
        path = data_root / relative
        present = path.is_file()
        results.append({"id": item["id"], "path": str(path), "present": present,
                        "hash_verified": bool(present and sha256_file(path) == item["sha256"])})
    return results


def inspect() -> dict:
    sys.path.insert(0, str(ROOT / "src"))
    from gems32.paths import data_dir
    core = inspect_core_data(json.loads((ROOT / "registry/data_manifest.json").read_text()), data_dir())
    pins = json.loads((ROOT / "registry/shared-template-pins.json").read_text())
    asset_root = ROOT / ".cache/template-assets"
    assets = []
    for item in pins["files"]:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe shared-template path")
        dest = asset_root / relative
        ok = dest.is_file() and sha256_file(dest) == item["sha256"]
        assets.append({"id": item["id"], "verified": bool(ok)})
    # This manifest explicitly records that the shared registry is incomplete.
    # A hash-valid snapshot alone must never become a full-registry PASS.
    audit = json.loads((ROOT / "evidence/historical_audit.json").read_text())
    witness = audit["lattice_witness"]
    stack = ROOT / ".cache/template-assets/data/prepared/features.npy"
    meta = ROOT / ".cache/template-assets/data/prepared/features.json"
    blockers = [
        "No explicitly user-assigned method lane or assignment source was identified; the parallel AP-1 lane was self-selected.",
        "The shared parallel-run registry is not complete; no all-registry surface/final-dot pass is possible.",
        "Archived GEMSDOE32-HIDE-RECOVER-v3.0 does not establish the requested truth-to-visible buffer or whole-segment scoring: 15,705 of 22,232 withheld-positive occurrences lie within 15 px of visible faults, and 76 component instances are partially scored (evidence/shared_split_geometry_20261028.json; upstream issue #60).",
        "The shared evaluator has additional unresolved empty-truth FP and evidence-label issues (#41, #61), and its writer silently binarizes probabilities (#37, #51). Do not privately fork the shared tools.",
        "The shared registry auditor can pass missing or tampered entries and calibrated rather than literal overlap (#63); the H-TRACE surface was checked only after dot placement. Prior pass claims cannot authorize a run.",
        "No owner-mirrored core data or sample is authenticated against the organizer; the mirrored sample disagrees with the public all-absence description.",
        "The parallel holdout/control comparison was not independently replayed and uses different refill rules.",
        "The cached prepared feature stack and metadata are absent or not verified here.",
        "At the historical champion's dot count, the literal registry lattice bound exceeds the 70% overlap limit.",
        "This review ran no experiment; archived AP-1 and H-TRACE research TIFFs fail the literal lattice gate and have no selector approval.",
    ]
    if not core or not all(item["hash_verified"] for item in core):
        blockers.append("Current core data is missing or differs from the pinned mirror; the historical restore receipt is not proof of current availability.")
    if not all(a["verified"] for a in assets):
        blockers.append("One or more pinned shared-template source assets are missing or changed; run the restore script.")
    return {
        "schema": "apartgems-preflight-v1",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "status": "BLOCKED",
        "verdict": "negative",
        "experiments_run": 0,
        "parallel_run_reported_experiments": 3,
        "prior_htrace_reported_experiments": 3,
        "weekly_slots_used": 0,
        "lane_assigned": False,
        "complete_parallel_registry": False,
        "current_core_data": core,
        "core_data_scope": "Hash verification against owner mirrors only, not organizer authentication. Historical restore receipts do not attest current presence.",
        "shared_assets": assets,
        "shared_assets_scope": "Pinned files only. They do not constitute a full runnable checkout or validated feature stack.",
        "feature_stack_present": stack.exists() and meta.exists(),
        "feature_stack_verified": False,
        "lattice_witness": {"uncovered_pixels": witness["uncovered_footprint_pixels"], "champion_sized_budget": witness["champion_sized_budget"], "minimum_overlap": witness["champion_sized_minimum_overlap"], "scope": "Conditional geometry bound, not a score and not proof against all smaller budgets."},
        "blockers": blockers,
        "candidate": None,  # no candidate created by this review
        "parallel_research_candidate": "evidence/parallel_candidate_audit.json",
        "submission_authorized": False,
    }


def main() -> int:
    result = inspect()
    print(json.dumps(result, indent=2, allow_nan=False))
    return 1 if result["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    sys.exit(main())
