#!/usr/bin/env python3
"""Standalone local format validator, not scientific or slot authorization.

Checks a conservative full-array finite [0, 1] condition relevant to the reported
portal range error, plus CRS/shape/geotransform against the
sample submission and a re-read of the bytes just written. A PASS is only a local
format diagnostic: it does not authenticate the reference, prove portal acceptance,
or authorize submission. Exit code 0 = diagnostic PASS, 1 = FAIL.

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
        if tpl.count != 1 or tpl.crs is None or tpl.driver != "GTiff":
            raise ValueError("Reference must be a single-band georeferenced GeoTIFF")
        sample_data = tpl.read(1, masked=True)
        foot = ~np.ma.getmaskarray(sample_data) & np.isfinite(sample_data.data)
        t_crs, t_shape, t_tf = tpl.crs, tpl.shape, tpl.transform
    if not foot.any():
        raise ValueError("Reference footprint is empty; cannot validate a submission")
    with rasterio.open(labels_path) as ds:
        if ds.count != 1 or (ds.crs, ds.shape, ds.transform) != (t_crs, t_shape, t_tf):
            raise ValueError("Catalogue grid does not match the reference grid")
        label_data = ds.read(1, masked=True)
        if (np.ma.getmaskarray(label_data) | ~np.isfinite(label_data.data))[foot].any():
            raise ValueError("Catalogue has invalid cells inside the reference footprint")
        labels = (label_data.data > 0) & foot
    with rasterio.open(path) as ds:
        arr = ds.read(1) if ds.count >= 1 else np.empty((0, 0))
        valid_pixels = ds.read_masks(1) != 0 if ds.count >= 1 else np.empty((0, 0), dtype=bool)
        meta = {"driver": ds.driver, "count": ds.count, "dtype": ds.dtypes[0] if ds.count else None,
                "crs": str(ds.crs), "shape": list(ds.shape),
                "transform": [float(x) for x in tuple(ds.transform)[:6]], "nodata_repr": str(ds.nodata),
                "self_contained": all(Path(f).resolve() == path.resolve() for f in ds.files)}
        same_grid = (ds.crs == t_crs and ds.shape == t_shape and ds.transform == t_tf)
    if arr.shape != foot.shape:
        return {"file": str(path), "pass": False, "error": f"shape {arr.shape} != template {foot.shape}", "meta": meta}
    in_foot = arr[foot]
    checks = {
        "geotiff": meta["driver"] == "GTiff",
        "single_band": meta["count"] == 1,
        "self_contained_geotiff": meta["self_contained"],
        "in_footprint_unmasked": bool(valid_pixels[foot].all()),
        "dtype_float32": meta["dtype"] == "float32",
        "crs_shape_transform_match_sample": bool(same_grid),
        "in_footprint_all_finite": bool(np.isfinite(in_foot).all()),
        "in_footprint_no_nan": int(np.isnan(in_foot).sum()) == 0,
        "in_footprint_no_inf": int(np.isinf(in_foot).sum()) == 0,
        "in_footprint_no_sentinel_lt_-1e30": int((in_foot < -1e30).sum()) == 0,
        "in_footprint_all_in_0_1": bool(((in_foot >= 0.0) & (in_foot <= 1.0)).all()),
        "conservative_whole_raster_finite_in_0_1": bool(
            (np.isfinite(arr) & (arr >= 0) & (arr <= 1)).all()),
        "zero_positive_pixels_on_catalogue": int(((arr > 0) & labels).sum()) == 0,
        "has_positive_predictions": int(((arr > 0) & foot).sum()) > 0,
    }
    finite_inside = in_foot[np.isfinite(in_foot)]
    outside = arr[~foot]
    outside_mode = ("no_exterior" if outside.size == 0 else
                    "all_zero" if bool((outside == 0).all()) else
                    "all_nan" if bool(np.isnan(outside).all()) else "mixed")
    return {"file": str(path), "pass": all(checks.values()), "checks": checks, "meta": meta,
            "positive_pixels_in_footprint": int(((arr > 0) & foot).sum()),
            "footprint_pixels": int(foot.sum()),
            "in_footprint_min": float(np.min(finite_inside)) if finite_inside.size else None,
            "in_footprint_max": float(np.max(finite_inside)) if finite_inside.size else None,
            "outside_footprint_mode": outside_mode,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size_bytes": path.stat().st_size}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--data-dir", type=Path, default=None)
    a = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from gems32.paths import data_dir
    ddir = a.data_dir or data_dir()
    ok = True
    for f in a.files:
        try:
            r = check(f, ddir / "sample_submission.tif", ddir / "labels.tif")
        except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
            print(f"LOCAL FORMAT FAIL: {f}: {exc}", file=sys.stderr)
            ok = False
            continue
        print(json.dumps(r, indent=1, allow_nan=False))
        print("LOCAL FORMAT PASS (not submission authorization)" if r["pass"] else "FAIL", f.name)
        ok = ok and r["pass"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
