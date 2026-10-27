#!/usr/bin/env python3
"""Standalone no-human-intervention validator for a submission GeoTIFF.

Checks exactly what the DrivenData portal rejected with
"Predicted values must be in range [0, 1]", plus CRS/shape/geotransform against the
sample submission and a re-read of the bytes just written. Exit code 0 = PASS, 1 = FAIL.

Usage:  python scripts/validate_submission.py docs/downloads/<file>-zeros.tif [more files...]
Data dir via $GEMS_DATA_DIR or --data-dir (needs sample_submission.tif + labels.tif).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio


def check(path: Path, sample: Path, labels_path: Path) -> dict:
    with rasterio.open(sample) as tpl:
        foot = np.isfinite(tpl.read(1))
        t_crs, t_shape, t_tf = tpl.crs, tpl.shape, tpl.transform
    with rasterio.open(labels_path) as ds:
        labels = (ds.read(1) > 0) & foot
    with rasterio.open(path) as ds:
        arr = ds.read(1) if ds.count >= 1 else np.empty((0, 0))
        meta = {"count": ds.count, "dtype": ds.dtypes[0] if ds.count else None,
                "crs": str(ds.crs), "shape": list(ds.shape),
                "transform": [float(x) for x in tuple(ds.transform)[:6]], "nodata_repr": str(ds.nodata)}
        same_grid = (ds.crs == t_crs and ds.shape == t_shape and ds.transform == t_tf)
    if arr.shape != foot.shape:
        return {"file": str(path), "pass": False, "error": f"shape {arr.shape} != template {foot.shape}", "meta": meta}
    in_foot = arr[foot]
    checks = {
        "single_band": meta["count"] == 1,
        "dtype_float32": meta["dtype"] == "float32",
        "crs_shape_transform_match_sample": bool(same_grid),
        "in_footprint_all_finite": bool(np.isfinite(in_foot).all()),
        "in_footprint_no_nan": int(np.isnan(in_foot).sum()) == 0,
        "in_footprint_no_inf": int(np.isinf(in_foot).sum()) == 0,
        "in_footprint_no_sentinel_lt_-1e30": int((in_foot < -1e30).sum()) == 0,
        "in_footprint_all_in_0_1": bool(((in_foot >= 0.0) & (in_foot <= 1.0)).all()),
        "whole_raster_all_in_0_1_or_nan_outside": bool(
            (np.nan_to_num(arr, nan=0.0) >= 0.0).all() and (np.nan_to_num(arr, nan=0.0) <= 1.0).all()),
        "zero_positive_pixels_on_catalogue": int(((arr > 0) & labels).sum()) == 0,
        "has_positive_predictions": int(((arr > 0) & foot).sum()) > 0,
    }
    outside = arr[~foot]
    outside_mode = ("all_zero" if bool((outside == 0).all()) else
                    "all_nan" if bool(np.isnan(outside).all()) else "mixed")
    return {"file": str(path), "pass": all(checks.values()), "checks": checks, "meta": meta,
            "positive_pixels_in_footprint": int(((arr > 0) & foot).sum()),
            "footprint_pixels": int(foot.sum()),
            "in_footprint_min": float(np.min(in_foot)), "in_footprint_max": float(np.max(in_foot)),
            "outside_footprint_mode": outside_mode,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size_bytes": path.stat().st_size}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--data-dir", type=Path, default=None)
    a = ap.parse_args()
    import os
    ddir = a.data_dir or Path(os.environ.get("GEMS_DATA_DIR", "/tmp/gems_data"))
    ok = True
    for f in a.files:
        r = check(f, ddir / "sample_submission.tif", ddir / "labels.tif")
        print(json.dumps(r, indent=1))
        print("PASS" if r["pass"] else "FAIL", f.name)
        ok = ok and r["pass"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
