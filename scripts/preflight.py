#!/usr/bin/env python3
"""Fail-closed current-run preflight; it never trains, writes TIFFs or selects slots."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from datetime import datetime, timezone

from audit_historical import ROOT, sha256_file


def inspect() -> dict:
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
        "No explicitly assigned single method lane or assignment source in this checkout.",
        "The shared parallel-run registry is not complete; no all-registry surface/final-dot pass is possible.",
        "No frozen comparable current-best leakage-safe holdout and paired confidence interval are available here.",
        "The cached prepared feature stack and metadata are absent or not verified here.",
        "At the historical champion's dot count, the literal registry lattice bound exceeds the 70% overlap limit.",
        "No new pre-placement surface, holdout result, candidate TIFF, byte validator result, or separate selector decision exists.",
    ]
    if not all(a["verified"] for a in assets):
        blockers.append("One or more pinned shared-template source assets are missing or changed; run the restore script.")
    return {
        "schema": "apartgems-preflight-v1",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "status": "BLOCKED",
        "verdict": "negative",
        "experiments_run": 0,
        "weekly_slots_used": 0,
        "lane_assigned": False,
        "complete_parallel_registry": False,
        "shared_assets": assets,
        "shared_assets_scope": "Pinned files only. They do not constitute a full runnable checkout or validated feature stack.",
        "feature_stack_present": stack.exists() and meta.exists(),
        "feature_stack_verified": False,
        "lattice_witness": {"uncovered_pixels": witness["uncovered_footprint_pixels"], "champion_sized_budget": witness["champion_sized_budget"], "minimum_overlap": witness["champion_sized_minimum_overlap"], "scope": "Conditional geometry bound, not a score and not proof against all smaller budgets."},
        "blockers": blockers,
        "candidate": None,
        "submission_authorized": False,
    }


def main() -> int:
    result = inspect()
    print(json.dumps(result, indent=2, allow_nan=False))
    return 1 if result["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    sys.exit(main())
