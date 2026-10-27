"""scripts/prepare_data.py

Inspect and validate the competition grid once data has been placed in data/.

Expected files (placed manually — see scripts/download_competition_data.sh):
  data/numeric_features.tif  multi-band feature stack (EPSG:32611, 100 m)
  data/labels.tif            fault labels on the same grid
  data/example_submission.tif (optional) format reference

Writes data/grid_reference.json with CRS, transform, shape, resolution, band
descriptions, nodata and dtype — consumed by src/generate_submission.py,
src/submission_writer.py and src/validate_submission.py.

This script prints only; it never downloads data and never invents numbers.
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    import rasterio
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "rasterio is required. Install with: pip install numpy rasterio"
    ) from exc

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
FEATURES = DATA_DIR / "numeric_features.tif"
LABELS = DATA_DIR / "labels.tif"
EXAMPLE = DATA_DIR / "example_submission.tif"
GRID_REF = DATA_DIR / "grid_reference.json"


def _band_descriptions(path: Path) -> list[dict]:
    out = []
    with rasterio.open(path) as src:
        for i in range(1, src.count + 1):
            tags = src.tags(i)
            out.append(
                {
                    "band": i,
                    "description": tags.get("description", ""),
                    "data_category": tags.get("data_category", ""),
                }
            )
    return out


def inspect_tif(path: Path) -> dict:
    with rasterio.open(path) as src:
        return {
            "path": str(path),
            "driver": src.driver,
            "width": src.width,
            "height": src.height,
            "count": src.count,
            "dtype": src.dtypes[0] if src.count else None,
            "crs": src.crs.to_string() if src.crs is not None else None,
            "transform": list(src.transform)[:6],
            "resolution_m": float(src.res[0]) if src.res else None,
            "nodata": src.nodata,
            "bounds": list(src.bounds),
            "bands": _band_descriptions(path),
        }


def main() -> int:
    print("=== GEMS data preparation ===")
    print(f"Repo root: {REPO_ROOT}")
    print(f"Data dir:  {DATA_DIR}")

    missing = [f for f in (FEATURES, LABELS) if not f.exists()]
    if missing:
        print("\nBLOCKER: required competition data not found:")
        for m in missing:
            print(f"  {m}")
        print("\nSee scripts/download_competition_data.sh for manual placement steps.")
        print("This sandbox cannot reach DrivenData (login wall) or Dropbox (not allowlisted).")
        return 1

    feature_info = inspect_tif(FEATURES)
    label_info = inspect_tif(LABELS)

    print("\n--- numeric_features.tif ---")
    for k, v in feature_info.items():
        print(f"  {k}: {v}")
    print("\n--- labels.tif ---")
    for k, v in label_info.items():
        print(f"  {k}: {v}")

    # Cross-check grid compatibility (the submission must match the labels grid).
    ok = True
    if feature_info["width"] != label_info["width"]:
        ok = False
        print(f"\nFAIL: width mismatch features={feature_info['width']} labels={label_info['width']}")
    if feature_info["height"] != label_info["height"]:
        ok = False
        print(f"FAIL: height mismatch features={feature_info['height']} labels={label_info['height']}")
    if feature_info["crs"] != label_info["crs"]:
        ok = False
        print(f"FAIL: CRS mismatch features={feature_info['crs']} labels={label_info['crs']}")
    if feature_info["transform"] != label_info["transform"]:
        ok = False
        print("FAIL: geotransform mismatch between features and labels")

    grid_reference = {
        "source": "inspected from data/numeric_features.tif and data/labels.tif",
        "crs": label_info["crs"],
        "transform": label_info["transform"],
        "width": label_info["width"],
        "height": label_info["height"],
        "count": 1,
        "dtype": "float32",
        "driver": "GTiff",
        "resolution_m": label_info["resolution_m"],
        "nodata": label_info["nodata"],
        "bounds": label_info["bounds"],
        "feature_bands": feature_info["bands"],
        "grids_compatible": bool(ok),
    }
    GRID_REF.write_text(json.dumps(grid_reference, indent=2))
    print(f"\nWrote grid reference: {GRID_REF}")
    print("Grids compatible:", ok)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
