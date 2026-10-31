#!/usr/bin/env python3
"""Reproducible check of the literal 70% registry-overlap gate (31 Oct 2026 review).

Question: does the literal rule "more than 70% of my dots fall within 3 px of one
registry raster's dots" separate a designed submission from random dots?

Method (same definition as src/gems32/registry_audit.py: candidate dots counted
inside the radius-3 disk dilation of the registry raster's dots):
  1. Footprint = finite cells of the official sample_submission.tif (pinned SHA).
  2. Lattice = 13GEMSDOE LATTICE_r13.tif (pinned SHA) restored by restore_data.py.
  3. For each candidate file: format facts + fraction of its dots within 3 px of lattice.
  4. Random null: uniform random dots inside the footprint, same N as each candidate,
     3 seeds, same overlap statistic.

Writes evidence/gate_density_check_20261031.json. Requires GEMS_DATA_DIR-style
restore under .cache/gems_data (run scripts/restore_data.py first).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".cache" / "gems_data"
SAMPLE = DATA / "sample_submission.tif"
LATTICE = DATA / "registry_focus" / "LATTICE_r13.tif"
LATTICE_SHA = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
SAMPLE_SHA = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"
OUT = ROOT / "evidence" / "gate_density_check_20261031.json"
CANDIDATES = [
    "docs/downloads/apartgems-v4-ridge-tmi-isohg-nms-q5pct-20261030.tif",
    "docs/downloads/apartgemsdoe2-h-ridge3-tensorfuse-37654-20261030-nan.tif",
    "docs/downloads/apartgemsdoe2-h-ridge3-tensorfuse-37654-20261030-zeros.tif",
    "docs/downloads/apartgemsdoe2-spmd-exp-2-sarpu-unified-34500dots-20261028T235800Z-2a51285d-nan.tif",
    "docs/downloads/apartgemsdoe2-sarpu-exp2-lefm-sarpu-37654dots-20261028T235500Z-25593731-zeros.tif",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def near_lattice_fraction(mask: np.ndarray, d_lat: np.ndarray) -> float:
    return float(((d_lat <= 3.0) & mask).sum() / mask.sum())


def main() -> int:
    assert sha256(SAMPLE) == SAMPLE_SHA, "sample_submission.tif SHA mismatch"
    assert sha256(LATTICE) == LATTICE_SHA, "LATTICE_r13.tif SHA mismatch"

    with rasterio.open(SAMPLE) as ds:
        s = ds.read(1)
        ref_shape, ref_tf, ref_crs = ds.shape, ds.transform, ds.crs
    foot = np.isfinite(s)
    with rasterio.open(LATTICE) as ds:
        lat_arr = ds.read(1)
    lat = np.isfinite(lat_arr) & (lat_arr > 0) & foot
    # Euclidean distance from every cell to the nearest lattice dot; <=3 px == disk3 dilation.
    d_lat = ndimage.distance_transform_edt(~lat)
    coverage = float(((d_lat <= 3.0) & foot).sum() / foot.sum())

    pool = np.flatnonzero(foot.ravel())
    result: dict = {
        "schema": "gate-density-check-v1",
        "date_utc": "2026-10-31",
        "footprint_px": int(foot.sum()),
        "lattice_dots_in_footprint": int(lat.sum()),
        "lattice_3px_footprint_coverage": round(coverage, 5),
        "literal_threshold": 0.70,
        "random_null": [],
        "candidates": [],
    }

    for n in (34500, 37654, 203418):
        vals = []
        for seed in range(3):
            pick = np.random.default_rng(seed).choice(pool, size=n, replace=False)
            m = np.zeros(foot.size, bool)
            m[pick] = True
            vals.append(near_lattice_fraction(m.reshape(foot.shape), d_lat))
        result["random_null"].append({"n_dots": n, "seeds": 3,
                                      "within_3px_of_lattice": [round(v, 5) for v in vals]})

    for rel in CANDIDATES:
        path = ROOT / rel
        if not path.is_file():
            result["candidates"].append({"file": rel, "status": "missing"})
            continue
        with rasterio.open(path) as ds:
            arr = ds.read(1)
            crs_ok = ds.crs == ref_crs
            shape_ok = ds.shape == ref_shape
            tf_ok = ds.transform == ref_tf
            dtype = ds.dtypes[0]
            nodata = ds.nodata
        inside = arr[foot]
        finite_in = np.isfinite(inside)
        outside = arr[~foot]
        dots = np.isfinite(arr) & (arr > 0) & foot
        result["candidates"].append({
            "file": rel,
            "sha256": sha256(path),
            "format": {
                "crs_matches_sample": bool(crs_ok),
                "shape_matches_sample": bool(shape_ok),
                "transform_matches_sample": bool(tf_ok),
                "dtype": dtype,
                "nodata": None if nodata is None else str(nodata),
                "inside_footprint_all_finite": bool(finite_in.all()),
                "inside_min": float(np.nanmin(inside)),
                "inside_max": float(np.nanmax(inside)),
                "inside_in_0_1": bool(((inside >= 0) & (inside <= 1))[finite_in].all()),
                "outside_policy": ("nan" if np.isnan(outside).all() else
                                   "zeros" if (outside == 0).all() else "other"),
            },
            "dots": int(dots.sum()),
            "within_3px_of_lattice": round(near_lattice_fraction(dots, d_lat), 5),
            "literal_gate_70pct_passed": bool(near_lattice_fraction(dots, d_lat) <= 0.70),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
