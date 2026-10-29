#!/usr/bin/env python3
"""Read-only geometry audit of the archived shared holdout split; no model or score.

Inputs must match the owner-mirror manifest. The receipt describes those bytes,
not an authenticated organizer data set. It does not fix or fork the shared
holdout evaluator. Run after ``scripts/restore_data.py``; this is intentionally
separate from any experiment and never emits a candidate TIFF.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt, label

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32 import holdout  # noqa: E402
from gems32.paths import data_dir  # noqa: E402


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    root = data_dir()
    manifest = json.loads((ROOT / "registry/data_manifest.json").read_text())
    pins = {x["id"]: x for x in manifest["files"]}
    ids = ("sample_submission", "labels", "ext_derived_sgmc_faults_100m_u8")
    inputs = {}
    for ident in ids:
        entry = pins[ident]
        rel = Path(entry["dest"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"Unsafe manifest path for {ident}")
        p = root / rel
        actual = sha256_file(p)
        if actual != entry["sha256"]:
            raise ValueError(f"Hash mismatch for {ident}")
        inputs[ident] = {"sha256": actual, "origin": "pinned owner mirror; not organizer-authenticated"}

    ctx = holdout.load_holdout_context(root)
    components, n = label(ctx.labels, structure=np.ones((3, 3), dtype=np.uint8))
    sizes = np.bincount(components.ravel(), minlength=n + 1)
    rows = []
    for cell in ctx.cells:
        y = cell.truth_coords[0] + int(cell.bbox[0].start)
        x = cell.truth_coords[1] + int(cell.bbox[1].start)
        if len(y) != cell.n_truth:
            raise AssertionError("Truth coordinates do not match cell count")
        if cell.visible_full is None or not cell.visible_full.any():
            raise ValueError(f"Missing visible catalogue for {cell.key}")
        # Full-grid distances avoid relying on the holdout's cropped bbox.
        dist = distance_transform_edt(~cell.visible_full)[y, x]
        counts = np.bincount(components[y, x], minlength=n + 1)
        selected = np.flatnonzero(counts[1:]) + 1
        total_source = int(sizes[selected].sum())
        partial = int(np.count_nonzero(counts[selected] < sizes[selected]))
        rows.append({
            "cell": cell.key,
            "withheld_positive_occurrences": int(cell.n_truth),
            "min_truth_to_visible_px": float(dist.min()) if len(dist) else None,
            "truth_within_15px_of_visible": int(np.count_nonzero(dist <= 15.0)),
            "source_connected_components_with_scored_truth": int(len(selected)),
            "partially_scored_component_instances": partial,
            "scored_fraction_of_those_components": float(cell.n_truth / total_source) if total_source else None,
        })
    result = {
        "schema": "apartgems-split-geometry-v1",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Geometry only: no predictions, holdout DTI, experiment, raster emission or slot. Eight draw/fold counts include repeated positive occurrences.",
        "shared_evaluator_file": "src/gems32/holdout.py",
        "shared_evaluator_sha256": sha256_file(ROOT / "src/gems32/holdout.py"),
        "upstream_report": "https://github.com/buffedlizard55-lab/GEMSDOE32/issues/60",
        "inputs": inputs,
        "collar_claim_px": 15,
        "cells": rows,
        "withheld_positive_occurrences": sum(x["withheld_positive_occurrences"] for x in rows),
        "truth_occurrences_within_15px_of_visible": sum(x["truth_within_15px_of_visible"] for x in rows),
        "partially_scored_component_instances": sum(x["partially_scored_component_instances"] for x in rows),
        "all_truth_more_than_15px_from_visible": all(
            r["min_truth_to_visible_px"] is not None and r["min_truth_to_visible_px"] > 15.0
            for r in rows
        ),
        "all_components_wholly_scored": all(r["partially_scored_component_instances"] == 0 for r in rows),
        "verdict": "negative",
    }
    # Print the replay; never overwrite the committed historical receipt.
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
