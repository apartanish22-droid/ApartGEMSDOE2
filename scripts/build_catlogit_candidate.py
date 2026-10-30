#!/usr/bin/env python3
"""H-CATLOGIT-OOF: quadrant-blocked logistic catalogue-likeness candidate (ApartGEMSDOE2).

Hypothesis (pre-registered in knowledge/preregistration_catlogit_20261030.md):
  Mapped faults in the GeoDAWN footprint leave a multi-physics signature (magnetic gradient,
  isostatic-gravity gradient, relief, strain, conductivity, depth-to-basement) that a *linear*
  discriminant trained on the USGS/INGENIOUS catalogue can rank in unmapped ground.

Method (no SGMC, no lattice, no holdout truth is used to build the surface):
  1. Read the 19 verified bands of ``training_features.tif`` on the 3730 x 3292 footprint
     (footprint = finite cells of ``sample_submission.tif``), robust-standardise each band
     (median/IQR from the footprint; sentinel -3.4e38 -> median).
  2. Leave-one-quadrant-out: for each footprint quadrant q, fit a logistic regression on the
     catalogue positives and a random 10x negative sample from the other three quadrants, then
     predict every pixel of quadrant q. The surface is therefore out-of-fold at quadrant scale.
  3. Catalogue pixels are excluded (the organizer scores with known USGS/INGENIOUS pixels masked,
     DrivenData forum clarification, 2026-09-16), so they get no dot.
  4. Emit the top ``N_DOTS`` non-catalogue pixels as a binary {0,1} dot raster, budget-matched to
     GEMSDOE32's 37,654-dot best file. Two NaN/zero-outside variants are written and audited by
     the repo's own ``gems32.submission.audit_geotiff`` (12-point checker).

Usage:  GEMS_DATA_DIR=.cache/gems_data python scripts/build_catlogit_candidate.py
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
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import holdout  # noqa: E402
from gems32.paths import data_dir  # noqa: E402
from gems32.submission import audit_geotiff  # noqa: E402

N_DOTS = 37654
N_NEG_PER_POS = 10
SEED = 20261030
SLUG = "catlogit-oof-37654dots"
LANE = "H-CATLOGIT-OOF"


def load_standardised_features(ddir: Path, foot: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """19-band robust-standardised design matrix on footprint cells (rows = footprint cells)."""
    cols = []
    with rasterio.open(ddir / "training_features.tif") as ds:
        names = [d.split(" - ")[0] if d else f"band{i + 1}" for i, d in enumerate(ds.descriptions)]
        for b in range(1, ds.count + 1):
            a = ds.read(b).astype(np.float32)
            x = a[foot]
            x = np.where(x < -1e30, np.nan, x)
            med = float(np.nanmedian(x))
            q1, q3 = np.nanpercentile(x, [25, 75])
            scale = float(q3 - q1) if float(q3 - q1) > 0 else float(np.nanstd(x)) or 1.0
            x = np.where(np.isfinite(x), x, med)
            x = (x - med) / scale
            lo, hi = np.percentile(x, [0.5, 99.5])
            cols.append(np.clip(x, lo, hi).astype(np.float32))
    X = np.stack(cols, axis=1)
    return X, names


def leave_one_quadrant_out_probability(X: np.ndarray, y: np.ndarray, quad: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    p = np.zeros(X.shape[0], dtype=np.float32)
    for q in (0, 1, 2, 3):
        train = quad != q
        pos = np.flatnonzero(train & y)
        neg_pool = np.flatnonzero(train & ~y)
        neg = rng.choice(neg_pool, size=min(neg_pool.size, N_NEG_PER_POS * pos.size), replace=False)
        idx = np.concatenate([pos, neg])
        clf = LogisticRegression(C=1.0, max_iter=1000, solver="lbfgs")
        clf.fit(X[idx], y[idx].astype(np.int8))
        test = np.flatnonzero(quad == q)
        p[test] = clf.predict_proba(X[test])[:, 1].astype(np.float32)
        print(f"quadrant {q}: train_pos={pos.size} train_neg={neg.size} test_px={test.size}", flush=True)
    return p


def build(ddir: Path, out_dir: Path, work_dir: Path) -> dict:
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
        template = ds.profile.copy()
    with rasterio.open(ddir / "labels.tif") as ds:
        labels_full = (ds.read(1) > 0) & foot
    ctx_quad = holdout.quadrant_ids(foot)
    quad = ctx_quad[foot]
    y = labels_full[foot]

    X, names = load_standardised_features(ddir, foot)
    p = leave_one_quadrant_out_probability(X, y, quad, SEED)
    p[y] = -1.0  # catalogue pixels are masked by the organizer: never dotted

    order = np.argpartition(-p, N_DOTS)[:N_DOTS]
    dot_flat = np.zeros(p.shape, dtype=bool)
    dot_flat[order] = True
    assert not (dot_flat & y).any(), "catalogue pixel selected"

    mask_full = np.zeros(foot.shape, dtype=bool)
    mask_full[foot] = dot_flat

    work_dir.mkdir(parents=True, exist_ok=True)
    np.save(work_dir / "catlogit_dots.npy", mask_full)
    np.save(work_dir / "catlogit_prob_footprint.npy", p)

    digest8 = hashlib.sha256(np.packbits(mask_full)).hexdigest()[:8]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"apartgemsdoe2-{SLUG}-{ts}-{digest8}"
    paths = {}
    base = template.copy()
    base.update(driver="GTiff", dtype="float32", count=1, compress="deflate", predictor=3, zlevel=9,
                tiled=True, blockxsize=256, blockysize=256)
    values = np.where(mask_full, np.float32(1.0), np.float32(0.0)).astype(np.float32)
    zeros = np.where(foot, values, np.float32(0.0)).astype(np.float32)
    nan = np.where(foot, values, np.float32(np.nan)).astype(np.float32)
    for mode, arr, nodata in (("zeros", zeros, None), ("nan", nan, np.nan)):
        path = out_dir / f"{stem}-{mode}.tif"
        prof = base.copy()
        prof.update(nodata=nodata)
        with rasterio.open(path, "w", **prof) as dst:
            dst.write(arr, 1)
        paths[mode] = path

    audits = {
        mode: audit_geotiff(paths[mode], foot, labels_full, mode=mode, template_tif=ddir / "sample_submission.tif")
        for mode in ("zeros", "nan")
    }
    receipt = {
        "lane": LANE,
        "slug": SLUG,
        "stem": stem,
        "timestamp_utc": ts,
        "dots": int(mask_full.sum()),
        "features": names,
        "quadrant_oof": True,
        "catalogue_pixels_excluded": True,
        "seed": SEED,
        "neg_per_pos": N_NEG_PER_POS,
        "files": {m: {"path": str(paths[m].relative_to(ROOT)), "sha256": audits[m]["sha256"],
                      "bytes": audits[m]["size_bytes"], "checks_passed": audits[m]["all_checks_passed"]}
                  for m in paths},
    }
    receipt_path = out_dir / f"{stem}-build.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    receipt["receipt_path"] = str(receipt_path.relative_to(ROOT))
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", type=Path, default=None)
    ap.add_argument("--out-dir", type=Path, default=ROOT / ".cache" / "candidates")
    ap.add_argument("--work-dir", type=Path, default=ROOT / ".cache" / "work" / "catlogit")
    args = ap.parse_args()
    receipt = build(args.data_dir or data_dir(), args.out_dir, args.work_dir)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
