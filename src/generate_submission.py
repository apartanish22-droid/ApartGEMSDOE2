"""src/generate_submission.py

Unique submission generator for the GEMS Prize Challenge.

HYPOTHESIS H1 (ranked #1 candidate — see docs/EXECUTIVE_SUMMARY.md):
  Layers: DEM (elevation band of numeric_features.tif) + radiometric bands
          (eU / eTh / K total-count style channels from the GeoDawn stack).
  Physical signature: curvature convergence (surface bending toward a common
  centre — extensional/dilation zones) coincident with a radiometric anomaly
  (hydrothermal alteration / fluid-path signature relative to local background).
  Why it catches catalogue-missing faults: the USGS / INGENIOUS catalogue maps
  traced surface scarps. Concealed/blind geothermal faults under thin cover show
  no scarp but can still express as (a) a subtle curvature convergence node and
  (b) a radiometric anomaly from alteration. The product targets exactly those.
  How it differs from this repo / prior GEMSDOE sites: prior submissions build
  dotted-ridge / scarp / openness / catalogue-distance maps (the "h33 dotted",
  "rung30 blind", "lidarscarp" families). H1 is the first non-scarp,
  non-catalogue, radiometric×curvature propensity map in this repo.

Output: single-band float32 GeoTIFF in [0,1], matching the reference grid
(CRS/shape/geotransform), 0 outside the study footprint. Written via
src/submission_writer.py and validated with src/validate_submission.py.

MODES:
  * real data (data/numeric_features.tif + data/labels.tif present): builds the
    H1 map on the true grid → OK to submit after validate_submission passes.
  * demo mode (no data): builds the same pipeline on a SYNTHETIC EPSG:32611
    100 m grid → a FORMAT DEMONSTRATION ONLY, NOT OK TO SUBMIT (shape/transform
    will not match the real submission grid).
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

from submission_writer import load_grid_spec, write_submission  # noqa: E402 (sibling import)

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
FEATURES = DATA_DIR / "numeric_features.tif"
LABELS = DATA_DIR / "labels.tif"
GRID_REF = DATA_DIR / "grid_reference.json"
ASSETS = REPO_ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

HYPOTHESIS = "H1"
SUBMISSION_NAME_TEMPLATE = "gems-h1-radiometric-curvature-convergence-{date}-{sha8}.tif"
NOTE = (
    "Unique H1 radiometric anomaly x DEM curvature-convergence propensity; "
    "not a copy of any prior GEMSDOE site submission."
)
assert len(NOTE) <= 140, f"note too long ({len(NOTE)} chars)"


def _band_index_by_keyword(src, keyword: str) -> int | None:
    """Find a band index whose description tag contains keyword (case-insensitive)."""
    kw = keyword.lower()
    for i in range(1, src.count + 1):
        desc = src.tags(i).get("description", "").lower()
        if kw in desc:
            return i - 1
    return None


def _normalize01(a: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Min-max normalize to [0,1] over valid (masked) pixels; 0 where invalid."""
    out = np.zeros_like(a, dtype=np.float32)
    v = np.where(mask, a, np.nan)
    lo = np.nanmin(v)
    hi = np.nanmax(v)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi == lo:
        return out
    out[mask] = np.clip((a[mask] - lo) / (hi - lo), 0.0, 1.0)
    return out


def _curvature_convergence(dem: np.ndarray, cell: float) -> np.ndarray:
    """Curvature convergence from a DEM.

    Convergence = -(z_xx + z_yy) i.e. negative Laplacian: positive where the
    surface bends toward a common centre (dilation/extensional nodes). A
    modelling choice for H1 — must be validated on the holdout, never assumed.
    Smoothed first with a 3x3 mean to suppress noise.
    """
    k = np.ones((3, 3), dtype=np.float64) / 9.0
    from scipy.ndimage import convolve

    d = convolve(dem.astype(np.float64), k, mode="nearest")
    dz_dx, dz_dy = np.gradient(d, cell)
    z_xx = np.gradient(dz_dx, cell, axis=1)
    z_yy = np.gradient(dz_dy, cell, axis=0)
    return -(z_xx + z_yy)


def _radiometric_anomaly(rad: np.ndarray, cell: float, radius_px: int = 15) -> np.ndarray:
    """Radiometric anomaly relative to local background (z-score in a window)."""
    from scipy.ndimage import uniform_filter1d

    r = rad.astype(np.float64)
    # separable local mean over radius_px px (~1.5 km at 100 m)
    m = uniform_filter1d(r, size=radius_px, axis=1, mode="nearest")
    m = uniform_filter1d(m, size=radius_px, axis=0, mode="nearest")
    s = uniform_filter1d(r * r, size=radius_px, axis=1, mode="nearest")
    s = uniform_filter1d(s, size=radius_px, axis=0, mode="nearest")
    var = np.maximum(s - m * m, 1e-6)
    std = np.sqrt(var)
    return (r - m) / std


def build_h1_map(features_path: Path, grid: object) -> tuple[np.ndarray, np.ndarray]:
    """Build the H1 propensity map [0,1] and a boolean footprint mask."""
    with rasterio.open(features_path) as src:
        dem_idx = _band_index_by_keyword(src, "elevation")
        if dem_idx is None:
            dem_idx = _band_index_by_keyword(src, "dem")
        if dem_idx is None:
            dem_idx = 0  # fall back to first band; document clearly
        rad_idxs = []
        for kw in ("radiometric", "eU", "eTh", "potassium", "uranium", "thorium", "total_count", "count"):
            idx = _band_index_by_keyword(src, kw)
            if idx is not None and idx not in rad_idxs:
                rad_idxs.append(idx)
        data = src.read()
        transform = src.transform
        nodata = src.nodata

    cell = float(abs(transform.a))
    dem = data[dem_idx].astype(np.float64)

    valid = np.isfinite(dem)
    if nodata is not None:
        valid &= data[dem_idx] != nodata

    conv = _curvature_convergence(dem, cell)
    conv[~valid] = np.nan

    anomaly = np.zeros_like(conv)
    if rad_idxs:
        rad_stack = np.stack([data[i].astype(np.float64) for i in rad_idxs])
        rad_valid = np.all(np.isfinite(rad_stack), axis=0) & valid
        if rad_stack.size:
            anomaly = np.nanmean(_radiometric_anomaly(np.nanmean(rad_stack, axis=0), cell), axis=0)
        anomaly[~rad_valid] = np.nan
    else:
        # No radiometric bands present: fall back to curvature only (documented degradation).
        anomaly[:] = 0.0

    conv_n = _normalize01(conv, valid)
    ano_n = _normalize01(anomaly, valid & ~np.isnan(anomaly))

    propensity = np.zeros_like(conv_n)
    use = valid & ~np.isnan(anomaly)
    propensity[use] = np.clip(conv_n[use] * ano_n[use], 0.0, 1.0)
    footprint = valid.copy()
    return propensity, footprint


def build_synthetic_demo() -> tuple[np.ndarray, np.ndarray, dict]:
    """Demo mode: synthetic EPSG:32611 100 m grid. NOT a real submission grid."""
    height, width = 1200, 1200
    cell = 100.0
    # origin chosen so it obviously does NOT claim to match the real grid
    transform = Affine(cell, 0, 500000.0, 0, -cell, 4500000.0)
    crs = "EPSG:32611"
    yy, xx = np.mgrid[0:height, 0:width]
    x = xx * cell
    y = yy * cell

    # Synthetic "concealed fault" nodes: curvature-convergence blobs + radiometric anomaly blobs
    rng = np.random.default_rng(42)
    conv = np.zeros((height, width))
    ano = np.zeros((height, width))
    for _ in range(18):
        cx = rng.integers(100, width - 100)
        cy = rng.integers(100, height - 100)
        s = rng.uniform(25, 60)
        gx = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * s * s))
        conv += gx
        ano += 0.6 * gx + 0.4 * rng.uniform(0, 0.3, (height, width)) * np.exp(
            -((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * (s * 1.5) ** 2)
        )
    # background radiogenic noise (mimicking process: uneven crustal radioactivity)
    ano += rng.normal(0, 0.15, (height, width))

    propensity = np.clip(
        _normalize01(conv, np.ones((height, width), dtype=bool))
        * _normalize01(ano, np.ones((height, width), dtype=bool)),
        0.0, 1.0,
    )
    footprint = np.ones((height, width), dtype=bool)
    grid = {"crs": crs, "transform": list(transform)[:6], "width": width, "height": height, "dtype": "float32"}
    return propensity, footprint, grid


def main() -> int:
    print(f"=== GEMS unique submission generator (hypothesis {HYPOTHESIS}) ===")
    real_data = FEATURES.exists() and LABELS.exists() and GRID_REF.exists()

    if real_data:
        print(f"Real data found: {FEATURES}, {LABELS}")
        grid = load_grid_spec(GRID_REF)
        propensity, footprint = build_h1_map(FEATURES, grid)
        mode = "real"
    else:
        print("DEMO MODE: no competition data in data/ — synthetic grid only.")
        print("See scripts/download_competition_data.sh for the manual placement blocker.")
        propensity, footprint, grid = build_synthetic_demo()
        mode = "demo"

    # Write via the validated writer (guarantees [0,1], no NaN inside footprint,
    # CRS/shape/transform match).
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sha8 = hashlib.sha256(propensity.tobytes()).hexdigest()[:8]
    out_name = SUBMISSION_NAME_TEMPLATE.format(date=now, sha8=sha8)
    out_path = ASSETS / out_name

    grid_spec = load_grid_spec(grid)
    report = write_submission(propensity, grid_spec, out_path, footprint=footprint)

    # Status banner file — makes it OBVIOUS whether OK to submit.
    status_ok = (
        mode == "real"
        and report["all_gates_pass"]
    )
    status_lines = [
        "GEMS SUBMISSION STATUS",
        "=====================",
        f"File: {out_name}",
        f"Mode: {mode}",
        f"Hypothesis: {HYPOTHESIS} — radiometric anomaly x DEM curvature convergence",
        f"SHA-256: {report['sha256']}",
        f"Note ({len(NOTE)} chars): {NOTE}",
        "",
        "VALIDATION REPORT:",
        json.dumps(report, indent=2),
        "",
        "VERDICT:",
    ]
    if status_ok:
        status_lines.append("OK TO SUBMIT — all validation gates passed on the real grid.")
    else:
        status_lines.append(
            "NOT OK TO SUBMIT — format demonstration on a synthetic grid. "
            "It will NOT match the real submission CRS/shape/geotransform. "
            "Place real data in data/ (see scripts/download_competition_data.sh), "
            "run scripts/prepare_data.py, then re-run this script."
        )
    status_lines.append("")
    status_lines.append("Leaderhead reference: best GEMSDOE focus-family score 0.2778 (GEMSDOE32); "
                        "live leaderboard high cited as 0.4413 (verify against live leaderboard).")
    (ASSETS / "SUBMISSION_STATUS.txt").write_text("\n".join(status_lines))

    print("\n".join(status_lines[:8]))
    print(f"\nWrote {out_path}")
    print(f"Validation: {'PASS' if report['all_gates_pass'] else 'FAIL/DEMO'}")
    print(f"OK to submit: {status_ok}")
    return 0 if status_ok else 0  # exit 0 either way; verdict is in the status file


if __name__ == "__main__":
    raise SystemExit(main())
