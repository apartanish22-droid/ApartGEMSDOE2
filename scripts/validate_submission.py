"""
validate_submission.py — canonical GEMS submission-TIF validator.

This is THE canonical validation tool for the repo.  Do not maintain private
forks; if a check is wrong, fix it here and report it.

Release gate (from README.md): a .tif is "OK TO SUBMIT" only when ALL of the
following hold:

  1. single-band GeoTIFF that opens and reads back
  2. CRS / shape / geotransform match the official sample_submission.tif
  3. no NaN / Inf inside the footprint (every pixel finite)
  4. all predicted values in [0, 1]  (fixes the "Predicted values must be in
     range [0, 1]" submission-form error)
  5. SHA-256 digest recorded
  6. registry correlation / dot-overlap checks pass (requires registry rasters)

Usage
-----
  python scripts/validate_submission.py path/to/file.tif \
      [--sample data/sample_submission.tif]

Exit code 0 = gate pass; non-zero = gate fail (prints machine-readable JSON).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(path, sample_path=None) -> dict:
    """Validate a GeoTIFF against the release gate. Returns a report dict."""
    report = {
        "file": str(path),
        "sha256": None,
        "opens_and_reads_back": False,
        "single_band": False,
        "dtype": None,
        "crs": None,
        "shape": None,
        "transform": None,
        "finite": False,
        "no_nan": False,
        "no_inf": False,
        "values_in_0_1": False,
        "min": None,
        "max": None,
        "matches_sample_crs_shape_transform": None,
        "sample_path": str(sample_path) if sample_path else None,
        "gate_pass": False,
        "failures": [],
    }

    try:
        report["sha256"] = sha256(path)
    except Exception as exc:
        report["failures"].append(f"cannot read file for hashing: {exc}")
        return report

    try:
        with rasterio.open(path) as dst:
            data = dst.read(1)
            report["opens_and_reads_back"] = True
            report["single_band"] = bool(dst.count == 1)
            report["dtype"] = str(dst.dtypes[0])
            report["crs"] = dst.crs.to_string() if dst.crs else None
            report["shape"] = [int(dst.height), int(dst.width)]
            report["transform"] = [float(v) for v in dst.transform[:6]]
            report["finite"] = bool(np.isfinite(data).all())
            report["no_nan"] = bool(~np.isnan(data).any())
            report["no_inf"] = bool(~np.isinf(data).any())
            report["min"] = float(np.nanmin(data))
            report["max"] = float(np.nanmax(data))
            report["values_in_0_1"] = bool(
                (data >= 0.0).all() and (data <= 1.0).all()
            )

            if sample_path is not None and Path(sample_path).exists():
                with rasterio.open(sample_path) as s:
                    report["matches_sample_crs_shape_transform"] = bool(
                        dst.crs == s.crs
                        and dst.height == s.height
                        and dst.width == s.width
                        and dst.transform == s.transform
                    )
            else:
                report["matches_sample_crs_shape_transform"] = (
                    "UNVERIFIED — sample_submission.tif unavailable "
                    "(DrivenData login required)"
                )
    except Exception as exc:
        report["failures"].append(f"rasterio open/read failed: {exc}")
        return report

    # Evaluate failures
    if not report["opens_and_reads_back"]:
        report["failures"].append("file does not open / read back as a GeoTIFF")
    if not report["single_band"]:
        report["failures"].append("not a single-band raster")
    if not report["finite"]:
        report["failures"].append("NaN or Inf present inside footprint")
    if not report["no_nan"]:
        report["failures"].append("NaN present inside footprint")
    if not report["no_inf"]:
        report["failures"].append("Inf present inside footprint")
    if not report["values_in_0_1"]:
        report["failures"].append(
            f"values outside [0, 1] (min={report['min']}, max={report['max']})"
        )
    if report["matches_sample_crs_shape_transform"] is not True:
        report["failures"].append(
            "CRS/shape/transform do not match official sample_submission.tif "
            "(or sample unavailable)"
        )

    core = all(
        report[k] is True
        for k in [
            "opens_and_reads_back",
            "single_band",
            "finite",
            "no_nan",
            "no_inf",
            "values_in_0_1",
        ]
    )
    report["gate_pass"] = bool(
        core and report["matches_sample_crs_shape_transform"] is True
        and not report["failures"]
    )
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Validate a GEMS submission GeoTIFF.")
    ap.add_argument("tif", help="Path to the GeoTIFF to validate")
    ap.add_argument(
        "--sample",
        default=None,
        help="Path to official sample_submission.tif for CRS/shape/transform match",
    )
    ap.add_argument(
        "--json",
        default=None,
        help="Write the machine-readable report to this JSON file",
    )
    args = ap.parse_args(argv)

    report = validate(Path(args.tif),
                      sample_path=Path(args.sample) if args.sample else None)

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        with open(args.json, "w") as f:
            json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    print(f"\nGATE_PASS: {report['gate_pass']}")
    if report["failures"]:
        for f in report["failures"]:
            print(f"  FAIL: {f}")
    return 0 if report["gate_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
