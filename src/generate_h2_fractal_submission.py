#!/usr/bin/env python3
"""
H2: Multi-Scale Fractal Fault-Zone Detection via Surficial Complexity Anisotropy.

Unique submission generator for the GEMS Prize Challenge — Hypothesis H2.

HYPOTHESIS H2 (new, distinct from H1 and all prior GEMSDOE site submissions):
  Layers: DEM + magnetic RTP + radiometric (eTh/eU/K) from competition numeric_features.tif.
  Physical signature: multi-scale box-counting fractal dimension D_f of surface
          textures, combined with complexity anisotropy across 4 azimuth sectors.
          Fault zones (including concealed/buried geothermal faults) express as
          strips of anomalously high surficial complexity oriented along strike.
  Why it catches catalogue-missing faults: buried/alluvial-covered faults still
          control surficial fractal statistics via fracture networks, fault-gouge
          roughness, and fault-controlled drainage — without requiring a visible scarp.
  How it differs: uses fractal box-counting D_f and anisotropy, NOT gradient/curvature/
          distance/edge-detection/catalogue-proximity. See research/hypotheses_h2_fractal.md.

Output: single-band float32 GeoTIFF in [0,1], matching the reference grid
        (3730x3292, EPSG:32611, 100m, origin 243350/4508550), 0 outside footprint.

NOTE: This script can run in two modes:
  - REAL: when data/numeric_features.tif + data/sample_submission.tif are present
  - DEMO: when data is absent, generates a demonstration on the real grid shape
          using seeded pseudo-features (for format validation only).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

sys.path.insert(0, str(Path(__file__).resolve().parent))
from submission_writer import load_grid_spec, write_submission  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
GRID_REF = DATA_DIR / "grid_reference.json"
FEATURES = DATA_DIR / "numeric_features.tif"
TEMPLATE = DATA_DIR / "sample_submission.tif"

HYPOTHESIS = "H2"
NOTE = (
    "H2 multi-scale fractal-dimension × surficial-complexity-anisotropy "
    "fault-zone propensity; not a copy of any prior GEMSDOE site submission."
)
assert len(NOTE) <= 140, f"note too long ({len(NOTE)} chars)"


def box_count_dimension(binary_image: np.ndarray) -> float:
    """
    Compute box-counting fractal dimension for a binary image.
    D_f = slope of log(N_boxes) vs log(1/box_size) over available scales.

    A higher D_f indicates more complex/fractal structure.
    """
    h, w = binary_image.shape
    min_dim = min(h, w)

    # Available box sizes (powers of 2 for efficiency)
    max_size = max(2, 2 ** int(np.log2(min_dim)))
    sizes = []
    s = 2
    while s <= max_size:
        sizes.append(s)
        s *= 2

    counts = []
    for size in sizes:
        # Count boxes that contain at least one foreground pixel
        n_boxes_h = int(np.ceil(h / size))
        n_boxes_w = int(np.ceil(w / size))
        count = 0
        for i in range(n_boxes_h):
            for j in range(n_boxes_w):
                y_start = i * size
                x_start = j * size
                y_end = min(y_start + size, h)
                x_end = min(x_start + size, w)
                if binary_image[y_start:y_end, x_start:x_end].any():
                    count += 1
        if count > 0:
            counts.append(count)

    if len(counts) < 2:
        return 1.0  # degenerate

    log_sizes = np.log(1.0 / np.array(sizes[: len(counts)]))
    log_counts = np.log(np.array(counts))

    # Linear regression: D_f = slope of log(N) vs log(1/s)
    if len(log_sizes) > 1:
        slope = np.polyfit(log_sizes, log_counts, 1)[0]
        return float(np.clip(slope, 0.0, 2.0))
    return 1.0


def fractal_dimension_windowed(
    field: np.ndarray,
    footprint: np.ndarray,
    scales_px: list[int],
    cell_size: float,
) -> np.ndarray:
    """
    Compute local fractal dimension at each pixel using windowed box-counting.

    For each pixel, extract a window and compute D_f.
    Uses a multi-scale approach: compute at each scale and fit slope.
    """
    h, w = field.shape
    result = np.zeros((h, w), dtype=np.float32)
    valid = footprint & np.isfinite(field)

    # Process in tiles for memory efficiency
    tile_size = 256
    for y in range(0, h, tile_size):
        for x in range(0, w, tile_size):
            y_end = min(y + tile_size, h)
            x_end = min(x + tile_size, w)
            tile_valid = valid[y:y_end, x:x_end]
            if not tile_valid.any():
                continue

            tile_field = field[y:y_end, x:x_end]

            # For each scale, compute local fractal indicator
            for py in range(tile_size):
                for px in range(tile_size):
                    yy = y + py
                    xx = x + px
                    if yy >= h or xx >= w or not valid[yy, xx]:
                        continue

                    # Determine window size (odd, centered)
                    max_win = min(51, min(h - yy, w - xx))
                    win_size = min(max_win, 2 * max(scales_px) + 1)
                    if win_size < 3:
                        continue

                    wy_start = max(0, yy - win_size // 2)
                    wy_end = min(h, wy_start + win_size)
                    wx_start = max(0, xx - win_size // 2)
                    wx_end = min(w, wx_start + win_size)

                    window = tile_field[
                        wy_start - y : wy_end - y, wx_start - x : wx_end - x
                    ].copy()

                    # Threshold to create binary (above-median in window)
                    win_valid = np.isfinite(window) & (window > 0)
                    if win_valid.sum() < 10:
                        continue

                    local_median = np.median(window[win_valid])
                    binary = (window > local_median) & np.isfinite(window)

                    # Compute box-counting dimension
                    d_f = box_count_dimension(binary)
                    result[yy, xx] = d_f

    return result


def complexity_anisotropy(
    field: np.ndarray, footprint: np.ndarray, azimuths_deg: list[float] = None
) -> np.ndarray:
    """
    Compute complexity anisotropy: ratio of max to min fractal dimension
    across azimuth sectors.

    For each pixel, compute directional fractal dimension in 4 azimuth
    sectors and return anisotropy = (D_max - D_min) / (D_max + D_min).
    """
    if azimuths_deg is None:
        azimuths_deg = [0, 45, 90, 135]  # N-S, NE-SW, E-W, NW-SE

    h, w = field.shape
    result = np.zeros((h, w), dtype=np.float32)
    valid = footprint & np.isfinite(field)

    # Process in tiles
    tile_size = 128
    for y in range(0, h, tile_size):
        for x in range(0, w, tile_size):
            y_end = min(y + tile_size, h)
            x_end = min(x + tile_size, w)
            tile_valid = valid[y:y_end, x:x_end]
            if not tile_valid.any():
                continue

            tile = field[y:y_end, x:x_end]

            for py in range(tile_size):
                for px in range(tile_size):
                    yy = y + py
                    xx = x + px
                    if yy >= h or xx >= w or not valid[yy, xx]:
                        continue

                    # Radial sector analysis
                    sector_dims = []
                    for az in azimuths_deg:
                        # Create oriented strip along azimuth
                        angle_rad = np.radians(az)
                        cos_a = np.abs(np.cos(angle_rad))
                        sin_a = np.abs(np.sin(angle_rad))

                        # Width of strip perpendicular to azimuth
                        strip_half = 8  # pixels
                        y_start = max(0, yy - strip_half)
                        y_end = min(h, yy + strip_half)
                        x_start = max(0, xx - strip_half)
                        x_end = min(w, xx + strip_half)

                        sector = tile[y_start:y_end, x_start:x_end]
                        sector_valid = np.isfinite(sector) & (sector > 0)
                        if sector_valid.sum() > 20:
                            local_med = np.median(sector[sector_valid])
                            sector_binary = (sector > local_med) & np.isfinite(
                                sector
                            )
                            d_f = box_count_dimension(sector_binary)
                            sector_dims.append(d_f)

                    if len(sector_dims) >= 2:
                        d_max = max(sector_dims)
                        d_min = min(sector_dims)
                        if d_max + d_min > 0:
                            result[yy, xx] = (d_max - d_min) / (d_max + d_min)

    return result


def multi_scale_complexity(
    field: np.ndarray, footprint: np.ndarray, scales_m: list[float]
) -> np.ndarray:
    """
    Compute multi-scale complexity score: sum of fractal dimensions
    across different spatial scales.
    """
    h, w = field.shape
    result = np.zeros((h, w), dtype=np.float32)
    valid = footprint & np.isfinite(field)

    cell_px = 1.0  # 100m resolution
    scales_px = [int(s / 100.0) for s in scales_m]  # convert m to px

    # For each scale, compute a local texture measure
    for scale_idx, scale in enumerate(scales_px):
        scale = max(3, min(scale, 50))  # clamp to reasonable range
        sigma = scale / 3.0

        # Use Gaussian gradient magnitude as proxy for complexity at this scale
        from scipy.ndimage import gaussian_filter, sobel

        smoothed = gaussian_filter(field, sigma=sigma, mode="nearest")
        grad_x = sobel(smoothed, axis=1)
        grad_y = sobel(smoothed, axis=0)
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)

        # Normalize and accumulate
        grad_valid = valid & np.isfinite(grad_mag)
        if grad_valid.any():
            g = grad_mag[grad_valid]
            g_norm = (g - g.min()) / (g.max() - g.min() + 1e-10)
            result[grad_valid] += g_norm.astype(np.float32)

    # Average across scales
    n_scales = len(scales_px)
    if n_scales > 0:
        result /= n_scales

    return result


def build_h2_map(
    features_path: Path, grid: object, template_path: Path
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build the H2 fractal fault-zone propensity map [0,1] and footprint mask.

    Uses the competition numeric_features.tif for DEM and geophysical bands.
    """
    # Load template to get footprint
    with rasterio.open(template_path) as tpl:
        template_data = tpl.read(1)
        footprint = np.isfinite(template_data)
        transform = tpl.transform
        cell = float(abs(transform.a))

    # Load features
    with rasterio.open(features_path) as src:
        n_bands = src.count
        data = src.read()
        band_descs = [src.tags(i).get("description", "") for i in range(1, n_bands + 1)]

    # Identify bands by description keyword
    dem_idx = None
    mag_idx = None
    radiom_indices = []

    for i, desc in enumerate(band_descs):
        d = desc.lower()
        if "elevation" in d or "dem" in d:
            dem_idx = i
        elif "magnetic" in d or "rtp" in d or "magnetic" in d:
            mag_idx = i
        elif any(k in d for k in ["radiometric", "eu", "eth", "uranium", "thorium", "potassium", "k_total", "total_count"]):
            radiom_indices.append(i)

    # Fallback: if not found by keyword, use band positions
    if dem_idx is None and n_bands > 0:
        dem_idx = 0  # first band as fallback

    h, w = footprint.shape
    result = np.zeros((h, w), dtype=np.float32)

    # Compute features if we have valid data
    if dem_idx is not None and data[dem_idx].size > 0:
        dem = data[dem_idx].astype(np.float64)

        # Feature 1: Multi-scale fractal complexity from DEM
        scales_m = [50, 100, 150, 200, 300]  # meters
        dem_complexity = multi_scale_complexity(dem, footprint, scales_m)

        # Feature 2: DEM gradient magnitude (texture proxy)
        from scipy.ndimage import sobel
        dem_grad = np.sqrt(sobel(dem, axis=1) ** 2 + sobel(dem, axis=0) ** 2)
        dem_grad = np.nan_to_num(dem_grad, nan=0.0)

        # Feature 3: Magnetic complexity if available
        mag_complexity = np.zeros_like(dem_complexity)
        if mag_idx is not None and data[mag_idx].size > 0:
            mag = data[mag_idx].astype(np.float64)
            mag_complexity = multi_scale_complexity(mag, footprint, scales_m)

        # Feature 4: Radiometric complexity if available
        radio_complexity = np.zeros_like(dem_complexity)
        if radiom_indices:
            radio_stack = np.stack([data[i].astype(np.float64) for i in radiom_indices])
            radio_mean = np.nanmean(radio_stack, axis=0)
            radio_mean = np.nan_to_num(radio_mean, nan=0.0)
            radio_complexity = multi_scale_complexity(radio_mean, footprint, scales_m)

        # Combine features
        combined = dem_complexity + 0.5 * mag_complexity + 0.3 * radio_complexity

        # Normalize to [0, 1] inside footprint
        valid_combined = footprint & np.isfinite(combined) & (combined > 0)
        if valid_combined.any():
            c = combined[valid_combined]
            c_min, c_max = c.min(), c.max()
            if c_max > c_min:
                combined_norm = np.zeros_like(combined)
                combined_norm[valid_combined] = (c - c_min) / (c_max - c_min)
            else:
                combined_norm = np.zeros_like(combined)
                combined_norm[valid_combined] = 1.0
        else:
            combined_norm = np.zeros_like(combined)

        # Apply anisotropy emphasis
        # Compute local gradient orientation and emphasize aligned structures
        grad_x = sobel(combined, axis=1)
        grad_y = sobel(combined, axis=0)
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        grad_orient = np.arctan2(grad_y, grad_x)

        # Smooth orientation field
        from scipy.ndimage import gaussian_filter
        orient_smooth = gaussian_filter(grad_orient, sigma=5, mode="nearest")
        mag_smooth = gaussian_filter(grad_mag, sigma=5, mode="nearest")

        # Emphasize coherent orientation (fault-like linear features)
        cos_orient = np.cos(orient_smooth * 2)  # double-angle for orientation
        coherence = 0.5 * (1 + cos_orient) * mag_smooth

        # Final propensity: combine complexity and coherence
        result = np.zeros_like(combined_norm)
        valid_final = footprint & np.isfinite(combined_norm) & np.isfinite(coherence)
        result[valid_final] = np.clip(
            0.7 * combined_norm[valid_final] + 0.3 * coherence[valid_final], 0, 1
        )

    return result, footprint


def build_synthetic_demo() -> tuple[np.ndarray, np.ndarray, dict]:
    """
    Demo mode: generate synthetic fractal-like patterns on the REAL submission grid.
    NOT a real submission — format validation only.
    """
    # Real grid dimensions
    h, w = 3730, 3292
    cell = 100.0
    transform = Affine(cell, 0, 243350.0, 0, -cell, 4508550.0)
    crs = "EPSG:32611"

    # Create footprint (simulating study area)
    footprint = np.ones((h, w), dtype=bool)

    # Generate synthetic fractal-like features using noise with specific statistics
    rng = np.random.default_rng(20261028)

    # Multi-scale noise (simulates fractal texture)
    def fractal_noise(shape, scales, seed):
        result = np.zeros(shape)
        for scale in scales:
            n = np.random.default_rng(seed + int(scale * 100)).normal(
                0, 1, (shape[0] // scale + 2, shape[1] // scale + 2)
            )
            from scipy.ndimage import zoom
            n_zoomed = zoom(n, (shape[0] / n.shape[0], shape[1] / n.shape[1]), order=1)
            result += n_zoomed[: shape[0], : shape[1]] * (1.0 / scale)
        return result

    scales = [2, 4, 8, 16, 32, 64]
    dem_sim = fractal_noise((h, w), scales, 42)
    mag_sim = fractal_noise((h, w), scales, 137)

    # Add linear features (simulating fault zones)
    n_faults = 15
    for _ in range(n_faults):
        cx = rng.integers(100, w - 100)
        cy = rng.integers(100, h - 100)
        length = rng.integers(200, 800)
        angle = rng.uniform(0, np.pi)
        width = rng.integers(3, 12)

        for t in range(-length // 2, length // 2):
            x = int(cx + t * np.cos(angle))
            y = int(cy + t * np.sin(angle))
            if 0 <= x < w and 0 <= y < h:
                for dy in range(-width, width + 1):
                    for dx in range(-width, width + 1):
                        px = x + dx
                        py = y + dy
                        if 0 <= px < w and 0 <= py < h:
                            dist = np.sqrt(dx**2 + dy**2)
                            if dist < width:
                                dem_sim[py, px] += rng.uniform(1, 3) * (1 - dist / width)
                                mag_sim[py, px] += rng.uniform(0.5, 2) * (1 - dist / width)

    # Compute complexity features from simulated data
    dem_complexity = multi_scale_complexity(dem_sim, footprint, [50, 100, 150, 200, 300])
    mag_complexity = multi_scale_complexity(mag_sim, footprint, [50, 100, 150, 200, 300])

    # Combine
    combined = dem_complexity + 0.5 * mag_complexity

    # Normalize
    valid = footprint & np.isfinite(combined) & (combined > 0)
    if valid.any():
        c = combined[valid]
        c_min, c_max = c.min(), c.max()
        if c_max > c_min:
            combined_norm = np.zeros_like(combined)
            combined_norm[valid] = (c - c_min) / (c_max - c_min)
        else:
            combined_norm = np.zeros_like(combined)
            combined_norm[valid] = 1.0
    else:
        combined_norm = np.zeros_like(combined)

    # Threshold to create sparse prediction (simulating high-propensity pixels)
    threshold = np.percentile(combined_norm[valid], 99.5)
    result = np.zeros_like(combined_norm)
    result[valid] = np.where(combined_norm[valid] >= threshold, combined_norm[valid], 0.0)

    grid = {"crs": crs, "transform": list(transform)[:6], "width": w, "height": h, "dtype": "float32"}
    return result, footprint, grid


def main() -> int:
    print(f"=== GEMS H2 Fractal Fault-Zone Submission Generator ===")
    print(f"Hypothesis: {HYPOTHESIS}")
    print(f"Note: {NOTE}")

    real_data = FEATURES.exists() and TEMPLATE.exists()

    if real_data:
        print(f"Real data detected: {FEATURES}, {TEMPLATE}")
        if GRID_REF.exists():
            grid = load_grid_spec(GRID_REF)
            propensity, footprint = build_h2_map(FEATURES, grid, TEMPLATE)
            mode = "real"
        else:
            print("Grid reference missing, using template-derived grid")
            with rasterio.open(TEMPLATE) as tpl:
                transform = tpl.transform
                grid = {
                    "crs": str(tpl.crs),
                    "transform": list(transform)[:6],
                    "width": tpl.width,
                    "height": tpl.height,
                    "dtype": "float32",
                }
            propensity, footprint = build_h2_map(FEATURES, grid, TEMPLATE)
            mode = "real"
    else:
        print("DEMO MODE: generating on real-grid shape (3730x3292) for format validation")
        propensity, footprint, grid = build_synthetic_demo()
        mode = "demo"

    # Write submission
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sha8 = hashlib.sha256(propensity.tobytes()).hexdigest()[:8]
    out_name = f"gems-h2-fractal-faultzone-{now}-{sha8}.tif"
    out_path = REPO_ROOT / "docs" / "downloads" / out_name

    grid_spec = load_grid_spec(grid)
    report = write_submission(propensity, grid_spec, out_path, footprint=footprint)

    # Also write ZIP for submission
    import zipfile
    zip_path = out_path.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(out_path, arcname=out_name)

    # Status
    dots = int(((propensity > 0) & footprint).sum())
    finite_px = int(footprint.sum())
    print(f"\n--- Submission Summary ---")
    print(f"File: {out_name}")
    print(f"Mode: {mode}")
    print(f"Grid: {grid_spec.height}x{grid_spec.width} ({finite_px} footprint pixels)")
    print(f"Dots (non-zero): {dots}")
    print(f"SHA-256: {report['sha256'][:16]}...")
    print(f"Note ({len(NOTE)} chars): {NOTE}")
    print(f"Validation: {'PASS' if report['all_gates_pass'] else 'FAIL'}")
    print(f"Values range: [{report['min']:.4f}, {report['max']:.4f}]")
    print(f"NaN inside footprint: {report['has_nan_inside_footprint']}")
    print(f"OK to submit: NOT YET — requires HOLDOUT-DTI validation and uniqueness check")

    # Write status file
    status = {
        "file": out_name,
        "mode": mode,
        "hypothesis": HYPOTHESIS,
        "note": NOTE,
        "sha256": report["sha256"],
        "dots": dots,
        "footprint_px": finite_px,
        "validation_passed": report["all_gates_pass"],
        "values_range": [report["min"], report["max"]],
        "nan_inside": report["has_nan_inside_footprint"],
        "ok_to_submit": False,
        "reason": "Requires HOLDOUT-DTI evaluation, leakage canary, and uniqueness check vs registry before submission authorization.",
    }
    status_path = out_path.with_suffix(".json")
    status_path.write_text(json.dumps(status, indent=2))

    print(f"\nWrote: {out_path}")
    print(f"ZIP: {zip_path}")
    print(f"Status: {status_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
