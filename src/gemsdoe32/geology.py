"""Structural geology, extensional tectonics, and geothermal vent corridor modeling."""

from __future__ import annotations

import math
from typing import Optional, Tuple

import numpy as np
from scipy.ndimage import gaussian_filter


def compute_dilation_tendency(
    strike_degrees: np.ndarray,
    shmin_azimuth_deg: float = 115.0,
) -> np.ndarray:
    """Compute normalized dilation tendency Td for fault strike orientations.

    In the Great Basin extensional tectonic province, regional Shmin is oriented ESE-WNW (~115°).
    Faults striking perpendicular to Shmin (strike ~025° to ~035° NNE) experience minimum normal
    stress and maximum dilation tendency, enhancing fluid transmissivity for geothermal systems.

    Formula:
        Td = sin^2(strike - Shmin)
    """
    strike_rad = np.radians(np.asarray(strike_degrees, dtype=np.float32))
    shmin_rad = np.radians(float(shmin_azimuth_deg))
    td = np.sin(strike_rad - shmin_rad) ** 2
    return np.clip(td, 0.0, 1.0)


def compute_slip_tendency(
    strike_degrees: np.ndarray,
    dip_degrees: float = 60.0,
    shmin_azimuth_deg: float = 115.0,
    stress_ratio_phi: float = 0.5,
) -> np.ndarray:
    """Compute normalized slip tendency Ts = tau / sigma_n under extensional stress state."""
    strike_rad = np.radians(np.asarray(strike_degrees, dtype=np.float32))
    shmin_rad = np.radians(float(shmin_azimuth_deg))
    angle_to_shmin = np.abs(strike_rad - shmin_rad)
    # Optimal normal faulting slip angle is typically ~30° from maximum principal stress (vertical in normal faulting)
    ts = np.abs(np.sin(2.0 * angle_to_shmin)) * np.sin(np.radians(dip_degrees))
    return np.clip(ts, 0.0, 1.0)


def compute_vent_corridor_prior(
    vent_locations_yx: np.ndarray,
    grid_shape: Tuple[int, int],
    corridor_strike_deg: float = 30.0,
    sigma_along_m: float = 3000.0,
    sigma_across_m: float = 800.0,
    pixel_m: float = 100.0,
) -> np.ndarray:
    """Compute anisotropic geothermal vent corridor density prior.

    Hydrothermal discharge and volcanic vents in the Great Basin align along fault-controlled
    structural corridors (e.g., N30°E strike). We apply an anisotropic Gaussian kernel
    extended along the strike direction.
    """
    height, width = grid_shape
    grid = np.zeros((height, width), dtype=np.float32)

    if len(vent_locations_yx) == 0:
        return grid

    # Place impulses at vent locations
    for y, x in vent_locations_yx:
        iy, ix = int(round(y)), int(round(x))
        if 0 <= iy < height and 0 <= ix < width:
            grid[iy, ix] += 1.0

    # Rotate coordinate grid by strike angle, blur with anisotropic sigmas, rotate back
    sigma_along_px = sigma_along_m / pixel_m
    sigma_across_px = sigma_across_m / pixel_m

    # Approximate via separable directional smoothing
    rad = np.radians(corridor_strike_deg)
    smoothed = gaussian_filter(grid, sigma=(sigma_across_px, sigma_across_px))
    # directional enhancement along strike
    for scale in [sigma_along_px * 0.5, sigma_along_px]:
        dy = int(round(scale * np.cos(rad)))
        dx = int(round(scale * np.sin(rad)))
        shifted_p = np.roll(np.roll(smoothed, dy, axis=0), dx, axis=1)
        shifted_n = np.roll(np.roll(smoothed, -dy, axis=0), -dx, axis=1)
        smoothed = 0.5 * smoothed + 0.25 * (shifted_p + shifted_n)

    # Normalize to [0, 1]
    max_val = float(np.max(smoothed))
    if max_val > 0.0:
        smoothed /= max_val
    return smoothed


def compute_stepover_stress(
    fault_mask: np.ndarray,
    search_radius_px: int = 15,
) -> np.ndarray:
    """Detect en-echelon fault step-overs and relay ramp stress concentrations.

    Overlapping fault tips transfer displacement across rock bridges, creating high
    fracture permeability anomalies.
    """
    faults = np.asarray(fault_mask, dtype=bool)
    # Density of fault tips within search radius
    smoothed_faults = gaussian_filter(faults.astype(np.float32), sigma=search_radius_px / 3.0)
    # Step-over regions have moderate overlapping density between disjoint tips
    stepover_prior = np.where((smoothed_faults > 0.05) & (smoothed_faults < 0.35) & (~faults), smoothed_faults, 0.0)
    max_val = float(np.max(stepover_prior))
    if max_val > 0.0:
        stepover_prior /= max_val
    return stepover_prior
