"""src/validate_submission.py

LEGACY diagnostic only: never authorizes a submission or authenticates a reference grid.

Gates (all must PASS):
  1. single band, GTiff driver
  2. CRS matches reference grid (EPSG:32611 expected)
  3. shape (height/width) matches
  4. geotransform matches
  5. no NaN inside the footprint
  6. all values inside the footprint in [0, 1]

Usage:
  python src/validate_submission.py assets/<submission>.tif [data/grid_reference.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GRID_REF = REPO_ROOT / "data" / "grid_reference.json"


def load_grid_ref(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_submission(tif_path: Path, grid_ref_path: Path = DEFAULT_GRID_REF) -> dict:
    if not tif_path.exists():
        return {"ok": False, "error": f"not found: {tif_path}"}
    if not grid_ref_path.exists():
        return {"ok": False, "error": f"grid reference not found: {grid_ref_path} (run scripts/prepare_data.py first)"}

    grid = load_grid_ref(grid_ref_path)
    report = {"path": str(tif_path), "grid_ref": str(grid_ref_path), "gates": {}, "ok": True}

    with rasterio.open(tif_path) as src:
        report["gates"]["driver"] = {
            "pass": src.driver == "GTiff",
            "actual": src.driver,
            "expected": "GTiff",
        }
        report["gates"]["band_count"] = {
            "pass": src.count == 1,
            "actual": src.count,
            "expected": 1,
        }
        report["gates"]["crs"] = {
            "pass": (src.crs is not None and src.crs.to_string() == grid["crs"]),
            "actual": src.crs.to_string() if src.crs is not None else None,
            "expected": grid["crs"],
        }
        report["gates"]["shape"] = {
            "pass": (src.height == grid["height"] and src.width == grid["width"]),
            "actual": [src.height, src.width],
            "expected": [grid["height"], grid["width"]],
        }
        report["gates"]["transform"] = {
            "pass": list(src.transform)[:6] == grid["transform"],
            "actual": list(src.transform)[:6],
            "expected": grid["transform"],
        }
        data = src.read(1).astype(np.float64)
        footprint = data != src.nodata if src.nodata is not None else np.ones(data.shape, dtype=bool)
        inside = data[footprint]
        report["gates"]["no_nan_inside_footprint"] = {
            "pass": bool(np.count_nonzero(np.isnan(inside)) == 0),
            "nan_count": int(np.count_nonzero(np.isnan(inside))),
        }
        report["gates"]["values_in_range_0_1"] = {
            "pass": bool(np.count_nonzero((inside < 0) | (inside > 1)) == 0),
            "min": float(np.nanmin(inside)) if inside.size else None,
            "max": float(np.nanmax(inside)) if inside.size else None,
            "below_zero": int(np.count_nonzero(inside < 0)),
            "above_one": int(np.count_nonzero(inside > 1)),
        }

    report["gates"]["all_pass"] = all(g["pass"] for g in report["gates"].values())
    # These legacy checks use the candidate's own nodata to infer a footprint;
    # they do not establish organizer-template provenance or any scientific gate.
    # Keep them for historical diagnostics only, never as upload authorization.
    report["format_checks_only_passed"] = bool(report["gates"]["all_pass"])
    report["ok"] = False
    report["submission_authorized"] = False

    # Human-readable verdict
    lines = [f"Validation of {tif_path.name}"]
    for name, g in report["gates"].items():
        if name == "all_pass":
            continue
        mark = "PASS" if g["pass"] else "FAIL"
        detail = ""
        if "actual" in g:
            detail = f" (actual={g['actual']}, expected={g['expected']})"
        lines.append(f"  [{mark}] {name}{detail}")
    lines.append("VERDICT: NOT AUTHORIZED — legacy checks do not authenticate a template or assess scientific gates. Use scripts/validate_raster.py for a read-back diagnostic.")
    print("\n".join(lines))
    return report


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 2
    tif_path = Path(argv[0])
    grid_ref = Path(argv[1]) if len(argv) > 1 else DEFAULT_GRID_REF
    report = validate_submission(tif_path, grid_ref)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
