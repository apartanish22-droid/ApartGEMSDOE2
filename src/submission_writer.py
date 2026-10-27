"""src/submission_writer.py

Write a competition-valid single-band GeoTIFF submission.

Requirements enforced (from the submission page and reference solution):
  * single band, GeoTIFF (GTiff) driver
  * float32 values clipped strictly to [0, 1]  (fixes the "Predicted values must be in range [0, 1]" error)
  * CRS, shape (height/width) and geotransform must match the submission format grid
  * pixels outside the study footprint are set to 0 (nodata outside = 0, consistent with "-zeros" submissions)
  * no NaN inside the footprint

Returns (and writes alongside the TIF) a SHA-256 of the raster bytes for the run card.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_bounds

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class GridSpec:
    crs: str
    transform: list[float]
    width: int
    height: int
    dtype: str = "float32"
    driver: str = "GTiff"
    count: int = 1


def load_grid_spec(grid_reference: Path | dict) -> GridSpec:
    if isinstance(grid_reference, dict):
        g = grid_reference
    else:
        g = json.loads(Path(grid_reference).read_text())
    return GridSpec(
        crs=g["crs"],
        transform=list(g["transform"]),
        width=int(g["width"]),
        height=int(g["height"]),
        dtype=str(g.get("dtype", "float32")),
    )


def validate_array(prediction: np.ndarray, grid: GridSpec, footprint: np.ndarray | None = None) -> dict:
    """Validate a prediction array before writing. Returns a report dict."""
    report = {
        "shape_ok": prediction.shape == (grid.height, grid.width),
        "shape": [int(prediction.shape[0]), int(prediction.shape[1])],
        "expected_shape": [int(grid.height), int(grid.width)],
        "dtype": str(prediction.dtype),
        "has_nan_inside_footprint": None,
        "min": float(np.nanmin(prediction)) if prediction.size else None,
        "max": float(np.nanmax(prediction)) if prediction.size else None,
        "in_range_0_1": None,
    }
    if not report["shape_ok"]:
        return report

    if footprint is None:
        footprint = np.ones((grid.height, grid.width), dtype=bool)
    inside = np.asarray(prediction)[footprint]
    report["has_nan_inside_footprint"] = bool(np.count_nonzero(np.isnan(inside)) > 0)
    report["in_range_0_1"] = bool(
        np.count_nonzero((inside < 0) | (inside > 1)) == 0
    )
    report["nan_count_inside_footprint"] = int(np.count_nonzero(np.isnan(inside)))
    report["below_zero_count"] = int(np.count_nonzero(inside < 0))
    report["above_one_count"] = int(np.count_nonzero(inside > 1))
    return report


def write_submission(
    prediction: np.ndarray,
    grid: GridSpec,
    out_path: Path | str,
    footprint: np.ndarray | None = None,
    nodata_outside: float = 0.0,
) -> dict:
    """Write the submission TIF. Clips to [0, 1], zeroes outside footprint."""
    prediction = np.asarray(prediction, dtype=np.float32)
    report = validate_array(prediction, grid, footprint)
    if not report["shape_ok"]:
        raise ValueError(
            f"shape mismatch: got {report['shape']}, expected {report['expected_shape']}"
        )

    if footprint is None:
        footprint = np.ones((grid.height, grid.width), dtype=bool)
    footprint = np.asarray(footprint, dtype=bool)

    out = np.zeros((grid.height, grid.width), dtype=np.float32)
    valid = footprint & ~np.isnan(prediction)
    vals = np.clip(prediction[valid], 0.0, 1.0)
    # Snap subnormal denormals to exactly 0 for a clean audit trail.
    vals[np.abs(vals) < 1e-12] = 0.0
    out[valid] = vals
    # pixels outside footprint -> nodata_outside (0). NaN inside footprint -> 0 too (fail-safe).
    out[~valid] = float(nodata_outside)

    final_report = validate_array(out, grid, footprint)
    final_report["sha256"] = None
    final_report["bytes_written"] = 0

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # NOTE: grid["transform"] is stored as list(src.transform)[:6], i.e.
    # rasterio's Affine storage order (a,b,c,d,e,f) = list(transform).
    # Reconstruct with Affine(*), NOT from_gdal (which expects GDAL order).
    transform = rasterio.transform.Affine(*grid.transform)
    with rasterio.open(
        out_path,
        "w",
        driver=grid.driver,
        height=grid.height,
        width=grid.width,
        count=grid.count,
        dtype=grid.dtype,
        crs=grid.crs,
        transform=transform,
        nodata=nodata_outside,
    ) as dst:
        dst.write(out, 1)
        dst.set_band_description(1, "fault_propensity_0_to_1")

    digest = hashlib.sha256(out_path.read_bytes()).hexdigest()
    final_report["sha256"] = digest
    final_report["bytes_written"] = int(out_path.stat().st_size)
    final_report["path"] = str(out_path)
    final_report["all_gates_pass"] = bool(
        final_report["shape_ok"]
        and not final_report["has_nan_inside_footprint"]
        and final_report["in_range_0_1"]
    )
    return final_report


__all__ = ["GridSpec", "load_grid_spec", "validate_array", "write_submission"]
