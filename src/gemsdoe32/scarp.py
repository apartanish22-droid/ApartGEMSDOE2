"""LiDAR DEM scarp extraction, multi-scale curvature, and topographic step detection."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter, sobel


def compute_profile_curvature(dem: np.ndarray, cell_size: float = 100.0) -> np.ndarray:
    """Compute profile curvature of digital elevation model.

    Profile curvature measures the rate of change of slope along the flow line,
    directly targeting break-of-slope knickpoints and fault scarps.
    """
    z = np.asarray(dem, dtype=np.float32)
    zy, zx = np.gradient(z, cell_size)
    zyy, zyx = np.gradient(zy, cell_size)
    zxy, zxx = np.gradient(zx, cell_size)

    p = zx**2 + zy**2
    p[p < 1e-7] = 1e-7

    # Profile curvature formula: -(zxx*zx^2 + 2*zxy*zx*zy + zyy*zy^2) / (p * (1 + p)^1.5)
    curv = -(zxx * (zx**2) + 2.0 * zxy * zx * zy + zyy * (zy**2)) / (p * (1.0 + p) ** 1.5)
    return np.nan_to_num(curv, nan=0.0, posinf=0.0, neginf=0.0)


def extract_scarp_features(
    dem: np.ndarray,
    cell_size: float = 100.0,
    scales: tuple[float, ...] = (1.0, 2.0, 4.0),
) -> dict[str, np.ndarray]:
    """Extract multi-scale topographic scarp indicator features from DEM."""
    features = {}
    base_dem = np.asarray(dem, dtype=np.float32)

    for scale in scales:
        smoothed = gaussian_filter(base_dem, sigma=scale)
        gy, gx = np.gradient(smoothed, cell_size)
        slope = np.sqrt(gx**2 + gy**2)

        # Scarp step magnitude (Sobel gradient of slope)
        slope_gy = sobel(slope, axis=0)
        slope_gx = sobel(slope, axis=1)
        step_mag = np.sqrt(slope_gx**2 + slope_gy**2)

        # Profile curvature
        prof_curv = compute_profile_curvature(smoothed, cell_size=cell_size)

        features[f"slope_s{scale}"] = slope
        features[f"step_mag_s{scale}"] = step_mag
        features[f"prof_curv_s{scale}"] = prof_curv

    return features
