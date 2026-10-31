#!/usr/bin/env python3
"""Build the V5 candidate GeoTIFF from the frozen v4 base and the pre-registered B = 2 exclusion.

Rule (pre-registered in knowledge/preregistration_v5_visible_exclusion_20261031.md):
  keep a v4 base dot only if it is more than 2 px (200 m) from every catalogue fault cell.

Output format: float32, single band, EPSG:32611, 3730 x 3292, template transform, values in {0, 1}
inside the footprint, 0 outside (not NaN). The zeros-outside choice follows the shared writer's
documented portal-safe option (src/gemsdoe32/submission.py). The official sample uses NaN outside.
Both conventions are reported in the run card because the portal's rule is unconfirmed.

    GEMS_DATA_DIR=.cache/gems_data python scripts/build_v5_candidate.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32.paths import data_dir  # noqa: E402

BASE = ROOT / "docs/downloads/apartgems-v4-ridge-tmi-isohg-nms-q5pct-20261030.tif"
NAME = "apartgems-v5-b2excl-zeros-20261031-DO-NOT-SUBMIT"
OUT_TIF = ROOT / "docs/downloads" / f"{NAME}.tif"
OUT_JSON = ROOT / "docs/downloads" / f"{NAME}.json"
NOTE = ("v4 ridge base minus dots within 2px of catalogue faults. HOLDOUT-DTI negative vs random "
        "control. DO NOT SUBMIT.")
RADIUS_EXCLUDE_PX = 2.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ddir = data_dir()
    with rasterio.open(ddir / "sample_submission.tif") as ref:
        foot = np.isfinite(ref.read(1))
        profile = ref.profile.copy()
        ref_transform = ref.transform
    with rasterio.open(ddir / "labels.tif") as ds:
        labels = (ds.read(1) == 1) & foot
    with rasterio.open(BASE) as ds:
        base = np.isfinite(ds.read(1)) & (ds.read(1) > 0) & foot
    base_dots = int(base.sum())
    d_lab = distance_transform_edt(~labels)
    keep = base & (d_lab > RADIUS_EXCLUDE_PX)
    out = np.where(foot, keep.astype(np.float32), np.float32(0.0)).astype(np.float32)

    profile.update(dtype="float32", count=1, nodata=None, compress="deflate", driver="GTiff")
    OUT_TIF.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(OUT_TIF, "w", **profile) as dst:
        dst.write(out, 1)
        dst.update_tags(submission_note=NOTE, submission_name=NAME)

    with rasterio.open(OUT_TIF) as back:
        a = back.read(1)
        checks = {
            "driver": back.driver,
            "band_count": back.count,
            "dtype": back.dtypes[0],
            "crs_epsg": back.crs.to_epsg(),
            "shape": [back.height, back.width],
            "transform_matches_sample": tuple(back.transform) == tuple(ref_transform),
            "nodata": back.nodata,
            "nan_count_total": int(np.isnan(a).sum()),
            "nan_inside_footprint": int(np.isnan(a[foot]).sum()),
            "values_in_unit_interval_inside_footprint": bool(((a[foot] >= 0) & (a[foot] <= 1)).all()),
            "all_cells_in_unit_interval": bool(((a >= 0) & (a <= 1)).all()),
            "nonzero_outside_footprint": int(((a != 0) & ~foot).sum()),
            "positive_dots": int((a > 0).sum()),
        }
    report = {
        "file": str(OUT_TIF.relative_to(ROOT)),
        "submission_name": NAME,
        "note": NOTE,
        "note_chars": len(NOTE),
        "sha256": sha256(OUT_TIF),
        "bytes": OUT_TIF.stat().st_size,
        "base_file": str(BASE.relative_to(ROOT)),
        "base_dots": base_dots,
        "excluded_dots_within_2px_of_catalogue": base_dots - int(keep.sum()),
        "dots": int(keep.sum()),
        "outside_convention": "zeros (0.0) outside footprint; NaN not used",
        "format_checks": checks,
        "ok_to_submit": "NO",
        "reason": "Holdout negative against random-thinning control; lattice gate fails (see run card).",
    }
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
