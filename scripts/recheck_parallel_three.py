#!/usr/bin/env python3
"""Read-only saved-byte/lattice recheck of three concurrent research TIFFs."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

from recheck_udsr import verify

ROOT = Path(__file__).resolve().parents[1]
CARDS = {
    "H-DIL-GRAV": "evidence/h_dil_grav_exp1_20261028T224631Z.json",
    "H-MAG-EDGE-SLOPE": "evidence/h_mag_edge_slope_exp2_20261028T224750Z.json",
    "H-DEPTH-COND": "evidence/h_depth_cond_exp3_20261028T224836Z.json",
}


def inspect_parallel_three() -> dict:
    """Recompute saved-byte checks, not models or holdout scores."""
    manifest = json.loads((ROOT / "evidence/history_manifest.json").read_text())
    sample = ROOT / "data/audit/mirror_sample.tif"
    results = {}
    for name, card_path in CARDS.items():
        card = json.loads((ROOT / card_path).read_text())
        candidate = ROOT / "docs/downloads" / card["raster"]
        result = verify(candidate, ROOT / "data/audit/lattice.tif", sample, card, manifest)
        with rasterio.open(candidate) as c, rasterio.open(sample) as s:
            values = c.read(1)
            valid = c.read_masks(1) != 0
            footprint = np.isfinite(s.read(1)) & (s.read_masks(1) != 0)
            result.update(
                dtype=c.dtypes[0],
                in_footprint_nan_cells=int(np.count_nonzero(np.isnan(values[footprint]))),
                in_footprint_nonfinite_cells=int(np.count_nonzero(~np.isfinite(values[footprint]))),
                in_footprint_masked_cells=int(np.count_nonzero(~valid[footprint])),
            )
        results[name] = result
    return {
        "schema": "apartgems-parallel-three-saved-byte-audit-v1",
        "scope": "Read-only saved-byte checks against the pinned owner mirror and one lattice. No holdout, registry-surface replay, experiment, new TIFF or slot.",
        "comparison": "Fraction of candidate positive pixels within 3 pixels of lattice positive pixels; this is directional.",
        "candidates": results,
    }


def main() -> int:
    result = inspect_parallel_three()
    result["checked_utc"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
