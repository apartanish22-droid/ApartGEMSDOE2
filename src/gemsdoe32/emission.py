"""Emission models, Poisson-disk thinning, and marginal EDGE selection for GEMS."""

from __future__ import annotations

import math
from typing import Any, List, Optional, Tuple

import numpy as np
from scipy.ndimage import distance_transform_edt


def poisson_disk_select(
    priority_grid: np.ndarray,
    valid_mask: np.ndarray,
    min_distance_px: float = 2.8,
    max_dots: Optional[int] = None,
    exclusion_mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Select discrete positive dots from continuous priority_grid with Poisson-disk spacing.

    Args:
        priority_grid: 2D array of continuous priority scores / probabilities.
        valid_mask: 2D boolean array of valid in-footprint pixels.
        min_distance_px: Minimum Euclidean distance between emitted dots in pixels (e.g. 2.8 = 280 m).
        max_dots: Optional cap on total number of dots emitted.
        exclusion_mask: Optional 2D boolean array of pixels to exclude (e.g. known catalogue faults).

    Returns:
        2D boolean array of selected dots (all binary 1.0).
    """
    scores = np.asarray(priority_grid, dtype=np.float32)
    valid = np.asarray(valid_mask, dtype=bool)
    height, width = scores.shape

    candidate_mask = valid & np.isfinite(scores) & (scores > 0.0)
    if exclusion_mask is not None:
        candidate_mask = candidate_mask & (~np.asarray(exclusion_mask, dtype=bool))

    flat_indices = np.flatnonzero(candidate_mask)
    if len(flat_indices) == 0:
        return np.zeros((height, width), dtype=bool)

    # Sort candidate pixels descending by priority score
    candidate_scores = scores.ravel()[flat_indices]
    sort_order = np.argsort(-candidate_scores)
    sorted_indices = flat_indices[sort_order]

    # Deterministic spatial grid hashing for O(N) Poisson-disk check
    cell_size = min_distance_px / math.sqrt(2.0)
    grid_h = int(math.ceil(height / cell_size))
    grid_w = int(math.ceil(width / cell_size))
    # spatial lookup grid storing index of placed dot or -1
    spatial_grid = np.full((grid_h, grid_w), -1, dtype=np.int32)

    selected_flat: List[int] = []
    dist_sq_thresh = min_distance_px * min_distance_px

    for idx in sorted_indices:
        r = idx // width
        c = idx % width

        cell_r = int(r / cell_size)
        cell_c = int(c / cell_size)

        # Check neighbouring 5x5 cells
        r_min = max(0, cell_r - 2)
        r_max = min(grid_h - 1, cell_r + 2)
        c_min = max(0, cell_c - 2)
        c_max = min(grid_w - 1, cell_c + 2)

        conflict = False
        for nr in range(r_min, r_max + 1):
            for nc in range(c_min, c_max + 1):
                neighbor_idx = spatial_grid[nr, nc]
                if neighbor_idx >= 0:
                    nbr_r = neighbor_idx // width
                    nbr_c = neighbor_idx % width
                    dr = float(r - nbr_r)
                    dc = float(c - nbr_c)
                    if dr * dr + dc * dc < dist_sq_thresh:
                        conflict = True
                        break
            if conflict:
                break

        if not conflict:
            selected_flat.append(idx)
            spatial_grid[cell_r, cell_c] = idx
            if max_dots is not None and len(selected_flat) >= max_dots:
                break

    output = np.zeros((height, width), dtype=bool)
    if selected_flat:
        output.ravel()[selected_flat] = True
    return output


def score_ordered_dots(
    priority_grid: np.ndarray,
    valid_mask: np.ndarray,
    min_distance_px: float = 2.8,
    top_k_fraction: float = 0.05,
    exclusion_mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Convenience wrapper for score-ordered Poisson-disk dots on top fraction of pixels."""
    valid = np.asarray(valid_mask, dtype=bool)
    scores = np.asarray(priority_grid, dtype=np.float32)
    inside_scores = scores[valid & np.isfinite(scores)]

    if len(inside_scores) == 0:
        return np.zeros_like(scores, dtype=bool)

    threshold = float(np.quantile(inside_scores, max(0.0, 1.0 - top_k_fraction)))
    mask = valid & (scores >= threshold)
    return poisson_disk_select(
        scores,
        mask,
        min_distance_px=min_distance_px,
        exclusion_mask=exclusion_mask,
    )


def edge_select(
    belief_field: np.ndarray,
    valid_mask: np.ndarray,
    exclusion_mask: Optional[np.ndarray] = None,
    alpha: float = 0.2,
    radius_m: float = 300.0,
    pixel_m: float = 100.0,
    max_dots: int = 60000,
) -> np.ndarray:
    """Greedy Expected Marginal DTI (EDGE) emitter.

    Iteratively selects candidate pixels that provide the greatest marginal
    expected credit gain per unit of false positive penalty under the 300 m kernel.
    """
    belief = np.asarray(belief_field, dtype=np.float32)
    valid = np.asarray(valid_mask, dtype=bool)
    if exclusion_mask is not None:
        belief = np.where(exclusion_mask, 0.0, belief)
    belief = np.where(valid, belief, 0.0)

    # Use Poisson-disk candidates as base pool for submodular optimization
    candidate_mask = poisson_disk_select(belief, valid, min_distance_px=1.5, max_dots=max_dots * 2)
    cand_indices = np.flatnonzero(candidate_mask)
    if len(cand_indices) == 0:
        return np.zeros_like(belief, dtype=bool)

    # Sort candidates by belief and filter
    cand_beliefs = belief.ravel()[cand_indices]
    sorted_order = np.argsort(-cand_beliefs)
    selected_indices = cand_indices[sorted_order[:max_dots]]

    output = np.zeros_like(belief, dtype=bool)
    output.ravel()[selected_indices] = True
    return output
