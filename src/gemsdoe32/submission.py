"""GeoTIFF submission generator and strict format validator for DrivenData DOE GEMS."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import rasterio


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": str(self.name),
            "passed": bool(self.passed),
            "detail": str(self.detail),
        }


@dataclass(frozen=True)
class ValidationReport:
    file_path: str
    sha256: str
    passed: bool
    checks: list[CheckResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": str(self.file_path),
            "sha256": str(self.sha256),
            "passed": bool(self.passed),
            "checks": [c.to_dict() for c in self.checks],
        }


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def validate_submission_geotiff(
    geotiff_path: Path,
    template_path: Path,
    strict_whole_array_finite: bool = False,
) -> ValidationReport:
    """Run comprehensive format and value validation on a candidate GeoTIFF."""
    checks = []
    sha256_hash = compute_sha256(geotiff_path)

    with rasterio.open(template_path) as tpl, rasterio.open(geotiff_path) as sub:
        # Check 1: Dimensions
        dim_ok = (sub.height, sub.width) == (tpl.height, tpl.width)
        checks.append(CheckResult("dimensions", dim_ok, f"shape {sub.shape} (expected {tpl.shape})"))

        # Check 2: Band count
        band_ok = sub.count == 1
        checks.append(CheckResult("band_count", band_ok, f"bands: {sub.count} (expected 1)"))

        # Check 3: CRS
        crs_ok = sub.crs == tpl.crs
        checks.append(CheckResult("crs", crs_ok, f"CRS: {sub.crs} (expected {tpl.crs})"))

        # Check 4: Geotransform
        transform_ok = sub.transform == tpl.transform
        checks.append(CheckResult("transform", transform_ok, f"transform matched template"))

        # Check 5: Dtype
        dtype_ok = sub.dtypes[0] == "float32"
        checks.append(CheckResult("dtype", dtype_ok, f"dtype: {sub.dtypes[0]} (expected float32)"))

        # Check 6: In-footprint values in [0, 1]
        tpl_data = tpl.read(1)
        valid_footprint = np.isfinite(tpl_data)
        sub_data = sub.read(1)

        inside_vals = sub_data[valid_footprint]
        finite_inside = np.all(np.isfinite(inside_vals))
        range_inside = False
        if finite_inside and len(inside_vals) > 0:
            min_val, max_val = float(inside_vals.min()), float(inside_vals.max())
            range_inside = (min_val >= 0.0) and (max_val <= 1.0)
            range_detail = f"in-footprint range [{min_val:.4f}, {max_val:.4f}], all finite"
        else:
            range_detail = "non-finite values or empty footprint detected inside valid mask"

        checks.append(CheckResult("in_footprint_range", range_inside and finite_inside, range_detail))

        # Check 7: Whole-array range (DrivenData portal compatibility)
        if strict_whole_array_finite:
            all_finite = np.all(np.isfinite(sub_data))
            all_in_range = all_finite and (float(sub_data.min()) >= 0.0) and (float(sub_data.max()) <= 1.0)
            checks.append(
                CheckResult(
                    "portal_safe_whole_array",
                    all_in_range,
                    f"whole-array range [{sub_data.min():.4f}, {sub_data.max():.4f}], finite={all_finite}",
                )
            )

    all_passed = all(c.passed for c in checks)
    return ValidationReport(file_path=str(geotiff_path), sha256=sha256_hash, passed=all_passed, checks=checks)


def write_submission_geotiff(
    predictions_2d: np.ndarray,
    template_path: Path,
    output_path: Path,
    outside_mode: str = "zeros",  # 'zeros' for portal-safe [0, 1] web form; 'nan' for published spec
    note: Optional[str] = None,
    compress: str = "deflate",
) -> Dict[str, Any]:
    """Write validated float32 GeoTIFF matching the official template.

    Args:
        predictions_2d: 2D array of predictions (probabilities or binary dots in [0, 1]).
        template_path: Path to sample_submission.tif.
        output_path: Output GeoTIFF path.
        outside_mode: 'zeros' (recommended for portal upload form) or 'nan' (spec).
        note: Short comment for DrivenData submission form (max 200 chars).
        compress: GeoTIFF compression method (e.g. 'deflate').

    Returns:
        Manifest dictionary with file metadata, sha256, and validation receipt.
    """
    preds = np.asarray(predictions_2d, dtype=np.float32)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(template_path) as tpl:
        profile = tpl.profile.copy()
        profile.update(
            dtype=rasterio.float32,
            count=1,
            compress=compress,
            nodata=None if outside_mode == "zeros" else float("nan"),
        )
        tpl_data = tpl.read(1)
        valid_footprint = np.isfinite(tpl_data)

        # Build output raster
        if outside_mode == "zeros":
            out_array = np.where(valid_footprint, preds, 0.0).astype(np.float32)
            # Ensure strictly in [0.0, 1.0]
            out_array = np.clip(out_array, 0.0, 1.0)
        else:
            out_array = np.where(valid_footprint, preds, np.nan).astype(np.float32)

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(out_array, 1)

    # Format verification
    report = validate_submission_geotiff(
        output_path,
        template_path,
        strict_whole_array_finite=(outside_mode == "zeros"),
    )

    if not report.passed:
        raise ValueError(f"Generated GeoTIFF failed validation: {report.to_dict()}")

    emitted_count = int(np.count_nonzero(out_array[valid_footprint] > 0.0))
    unique_id = report.sha256[:12]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    if note is None:
        note = f"GEMSDOE32 | id:{unique_id} | dots:{emitted_count} | mode:{outside_mode}"
    if len(note) > 200:
        note = note[:197] + "..."

    manifest = {
        "file_path": str(output_path),
        "file_name": str(output_path.name),
        "unique_id": str(unique_id),
        "sha256": str(report.sha256),
        "timestamp_utc": str(timestamp),
        "outside_mode": str(outside_mode),
        "portal_compliant_range": bool(outside_mode == "zeros"),
        "emitted_dots_count": int(emitted_count),
        "note": str(note),
        "validation_passed": bool(report.passed),
        "validation_report": report.to_dict(),
    }

    # Write sidecar JSON
    sidecar = output_path.with_suffix(".json")
    sidecar.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    return manifest
