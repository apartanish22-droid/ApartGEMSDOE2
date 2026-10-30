#!/usr/bin/env python3
"""Single-feature top-N candidate (no fitting): dots = N highest (or lowest) non-catalogue footprint
cells of one verified training band, written as a binary {0,1} GeoTIFF in both repo conventions.

The band is chosen by a stated rule BEFORE the run (see knowledge/preregistration_catlogit_20261030.md),
never by the SGMC proxy. Catalogue pixels are excluded (organizer masks them in scoring).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32.paths import data_dir  # noqa: E402
from gems32.submission import audit_geotiff  # noqa: E402


def band_index(ds, name: str) -> int:
    for i, d in enumerate(ds.descriptions, start=1):
        if d and d.split(" - ")[0] == name:
            return i
    raise ValueError(f"band {name!r} not found")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--band", required=True)
    ap.add_argument("--direction", choices=["high", "low"], required=True)
    ap.add_argument("--n", type=int, default=37654)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--lane", required=True)
    ap.add_argument("--out-dir", type=Path, default=ROOT / ".cache" / "candidates")
    ap.add_argument("--data-dir", type=Path, default=None)
    args = ap.parse_args()
    ddir = args.data_dir or data_dir()
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
        template = ds.profile.copy()
    with rasterio.open(ddir / "labels.tif") as ds:
        labels = (ds.read(1) > 0) & foot
    with rasterio.open(ddir / "training_features.tif") as ds:
        b = band_index(ds, args.band)
        v = ds.read(b).astype(np.float64)
    v = np.where(v < -1e30, np.nan, v)
    score = v if args.direction == "high" else -v
    cand = foot & ~labels & np.isfinite(score)
    idx = np.flatnonzero(cand.ravel())
    top = idx[np.argpartition(-score.ravel()[idx], args.n)[: args.n]]
    mask = np.zeros(foot.size, dtype=bool)
    mask[top] = True
    mask = mask.reshape(foot.shape)
    assert not (mask & labels).any()

    digest8 = hashlib.sha256(np.packbits(mask)).hexdigest()[:8]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"apartgemsdoe2-{args.slug}-{ts}-{digest8}"
    base = template.copy()
    base.update(driver="GTiff", dtype="float32", count=1, compress="deflate", predictor=3, zlevel=9,
                tiled=True, blockxsize=256, blockysize=256)
    vals = mask.astype(np.float32)
    arrays = {"zeros": (np.where(foot, vals, np.float32(0.0)).astype(np.float32), None),
              "nan": (np.where(foot, vals, np.float32(np.nan)).astype(np.float32), np.nan)}
    paths = {}
    for mode, (arr, nodata) in arrays.items():
        p = args.out_dir / f"{stem}-{mode}.tif"
        prof = base.copy()
        prof.update(nodata=nodata)
        with rasterio.open(p, "w", **prof) as dst:
            dst.write(arr, 1)
        paths[mode] = p
    audits = {m: audit_geotiff(paths[m], foot, labels, mode=m, template_tif=ddir / "sample_submission.tif")
              for m in paths}
    receipt = {
        "lane": args.lane, "slug": args.slug, "stem": stem, "timestamp_utc": ts,
        "band": args.band, "direction": args.direction, "dots": int(mask.sum()), "n_requested": args.n,
        "catalogue_pixels_excluded": True,
        "files": {m: {"path": str(paths[m].relative_to(ROOT)), "sha256": audits[m]["sha256"],
                      "bytes": audits[m]["size_bytes"], "checks_passed": audits[m]["all_checks_passed"]}
                  for m in paths},
    }
    rp = args.out_dir / f"{stem}-build.json"
    rp.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
