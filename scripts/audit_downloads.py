"""Audit every downloadable/submission-candidate GeoTIFF against the canonical grid.

Checks (no human inspection): EPSG:32611, 3292 x 3730, 100 m, origin (243350, 4508550),
single band, float32, NaN count, whole-array range, nonzero count, sha256.
Writes a JSON receipt to evidence/download_audit_<date>.json. Verdicts are
technical only: a PASS here is NOT scientific or weekly-slot authorization.

Usage: .venv/bin/python scripts/audit_downloads.py [--out evidence/download_audit_20261028.json]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
W, H, RES, X0, Y0 = 3292, 3730, 100.0, 243350.0, 4508550.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def audit(path: Path) -> dict:
    with rasterio.open(path) as ds:
        t = ds.transform
        grid_ok = (
            ds.crs is not None and ds.crs.to_epsg() == 32611
            and (ds.width, ds.height) == (W, H)
            and abs(t.a - RES) < 1e-6 and abs(t.e + RES) < 1e-6
            and abs(t.c - X0) < 1e-3 and abs(t.f - Y0) < 1e-3
        )
        a = ds.read(1).astype("float64") if ds.count == 1 else None
        single = ds.count == 1 and ds.dtypes[0] == "float32"
    if a is None:
        return {"file": str(path.relative_to(ROOT)), "error": "not single-band"}
    finite = np.isfinite(a)
    nan_n = int((~finite).sum())
    fin_vals = a[finite]
    in_range = bool(fin_vals.size) and float(fin_vals.min()) >= 0.0 and float(fin_vals.max()) <= 1.0
    whole_portal_safe = nan_n == 0 and in_range
    reasons = []
    if not grid_ok:
        reasons.append("grid mismatch (CRS/shape/transform)")
    if not single:
        reasons.append("not single-band float32")
    if nan_n:
        reasons.append(f"{nan_n} NaN pixels (portal range rule is whole-array [0,1])")
    if not in_range:
        reasons.append("values outside [0,1]")
    return {
        "file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "grid_match": bool(grid_ok),
        "single_band_float32": bool(single),
        "nan_pixels": nan_n,
        "min": float(fin_vals.min()) if fin_vals.size else None,
        "max": float(fin_vals.max()) if fin_vals.size else None,
        "nonzero_pixels": int((fin_vals > 0).sum()),
        "portal_whole_array_safe": bool(whole_portal_safe),
        "technical_verdict": "TECHNICAL-PASS" if (grid_ok and single and whole_portal_safe) else "TECHNICAL-FAIL",
        "reasons": reasons,
        "scientific_verdict": "NOT ASSESSED HERE (no holdout receipt; see docs/research/repo-review-20261028.md)",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "download_audit_20261028.json")
    args = ap.parse_args()
    paths = sorted(Path(p) for p in glob.glob(str(ROOT / "docs/downloads/*.tif")) + glob.glob(str(ROOT / "assets/*.tif")))
    rows = [audit(p) for p in paths]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"canonical_grid": dict(crs="EPSG:32611", width=W, height=H, res_m=RES, origin=[X0, Y0]),
                                    "files": rows}, indent=2) + "\n")
    for r in rows:
        print(f"{r.get('technical_verdict', 'ERROR'):14s} {r['file']}  nan={r.get('nan_pixels')}  grid={r.get('grid_match')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
