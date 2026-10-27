"""Spatially blocked holdout and hide-and-recover validation protocols."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

from .emission import poisson_disk_select
from .metric import compute_dti, compute_dti_components


@dataclass
class FoldSplit:
    fold_idx: int
    train_mask: np.ndarray
    val_mask: np.ndarray


def create_spatial_block_folds(
    shape: Tuple[int, int],
    valid_mask: np.ndarray,
    n_rows: int = 4,
    n_cols: int = 4,
    n_splits: int = 4,
    seed: int = 42,
) -> List[FoldSplit]:
    """Partition the valid study area into spatially disjoint blocks to prevent autocorrelation leakage."""
    height, width = shape
    block_h = int(np.ceil(height / n_rows))
    block_w = int(np.ceil(width / n_cols))

    rng = np.random.RandomState(seed)
    block_assignments = rng.randint(0, n_splits, size=(n_rows, n_cols))

    folds: List[FoldSplit] = []
    for f in range(n_splits):
        val_grid = np.zeros(shape, dtype=bool)
        for r in range(n_rows):
            r_start = r * block_h
            r_end = min(height, (r + 1) * block_h)
            for c in range(n_cols):
                c_start = c * block_w
                c_end = min(width, (c + 1) * block_w)
                if block_assignments[r, c] == f:
                    val_grid[r_start:r_end, c_start:c_end] = True

        val_mask = val_grid & valid_mask
        train_mask = valid_mask & (~val_mask)
        folds.append(FoldSplit(fold_idx=f, train_mask=train_mask, val_mask=val_mask))

    return folds


def evaluate_hide_and_recover(
    model_predictions: np.ndarray,
    ground_truth: np.ndarray,
    valid_mask: np.ndarray,
    heldout_positive_mask: np.ndarray,
    spacing_px: float = 2.8,
) -> Dict[str, float]:
    """Evaluate candidate predictions on hidden ground truth positives with known components masked.

    Simulates the competition's hidden discovery set where known catalogue faults are masked out.
    """
    # Exclude known catalogue faults from emitted candidate dots
    known_faults = ground_truth & (~heldout_positive_mask)

    emitted_dots = poisson_disk_select(
        model_predictions,
        valid_mask=valid_mask,
        min_distance_px=spacing_px,
        exclusion_mask=known_faults,
    )

    # Evaluate against the held-out positive ground truth
    comp = compute_dti_components(
        emitted_dots,
        ground_truth=heldout_positive_mask,
        valid_mask=valid_mask,
    )

    return {
        "dti_score": comp.score,
        "tp_weight": comp.tp_weight,
        "fp_weight": comp.fp_weight,
        "fn_weight": comp.fn_weight,
        "emitted_dot_count": float(np.count_nonzero(emitted_dots)),
    }
