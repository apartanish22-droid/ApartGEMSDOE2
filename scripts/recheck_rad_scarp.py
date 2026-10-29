#!/usr/bin/env python3
"""Read-only saved-byte / lattice recheck of the archived RAD-SCARP TIFF."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

from recheck_udsr import verify

ROOT = Path(__file__).resolve().parents[1]


def inspect_rad_scarp() -> dict:
    """Recompute the receipt without writing files or running a model."""
    card = json.loads((ROOT / "evidence/rad_scarp_run_card_20261028.json").read_text())
    manifest = json.loads((ROOT / "evidence/history_manifest.json").read_text())
    result = verify(
        ROOT / card["raster"], ROOT / "data/audit/lattice.tif",
        ROOT / "data/audit/mirror_sample.tif", card, manifest,
    )
    with rasterio.open(ROOT / card["raster"]) as candidate, rasterio.open(ROOT / "data/audit/mirror_sample.tif") as sample:
        values = candidate.read(1)
        valid = candidate.read_masks(1) != 0
        footprint = np.isfinite(sample.read(1)) & (sample.read_masks(1) != 0)
        result.update(
            dtype=candidate.dtypes[0],
            in_footprint_nan_cells=int(np.count_nonzero(np.isnan(values[footprint]))),
            in_footprint_nonfinite_cells=int(np.count_nonzero(~np.isfinite(values[footprint]))),
            in_footprint_masked_cells=int(np.count_nonzero(~valid[footprint])),
        )
    result.update(
        historical_candidate="RAD-SCARP",
        scope="Read-only saved-byte check against the pinned owner mirror and one lattice. No holdout, registry-surface replay, experiment, new TIFF or slot.",
    )
    return result


def main() -> int:
    result = inspect_rad_scarp()
    result["checked_utc"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
