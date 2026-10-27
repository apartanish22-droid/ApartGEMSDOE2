"""Exact Distance-Weighted Tversky Index (DTI) metric for DOE GEMS Prize.

The published GEMS evaluation metric computes a distance-weighted Tversky index
using a triangular kernel with support radius R = 300 m, alpha = 0.2, and beta = 0.8:
    DTI = T / (T + alpha * F + beta * G + epsilon)
where:
    T = distance-weighted true positive credit delivered to ground truth labels
    F = distance-weighted false positive penalty of emitted predictions
    G = unweighted ground truth count (or distance-weighted ground truth mass)
    alpha = 0.2, beta = 0.8
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Tuple

import numpy as np
from scipy.ndimage import distance_transform_edt

DEFAULT_RADIUS_M = 300.0
DEFAULT_PIXEL_M = 100.0
DEFAULT_ALPHA = 0.2
DEFAULT_BETA = 0.8
DEFAULT_EPSILON = 1e-7


@dataclass(frozen=True)
class DTIComponents:
    """Sufficient statistics and the resulting distance-weighted Tversky score."""
    tp_weight: float
    fp_weight: float
    fn_weight: float
    score: float


def triangular_kernel(distance_m: float, radius_m: float = DEFAULT_RADIUS_M) -> float:
    """Return max(1 - distance / radius, 0) for non-negative distance."""
    if distance_m < 0:
        raise ValueError("distance_m must be non-negative")
    if radius_m <= 0:
        raise ValueError("radius_m must be positive")
    return max(0.0, 1.0 - float(distance_m) / float(radius_m))


def dti_from_counts(
    tp_weight: float,
    fp_weight: float,
    fn_weight: float,
    *,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    epsilon: float = DEFAULT_EPSILON,
) -> float:
    """Compute published weighted Tversky ratio from sufficient statistics."""
    if min(tp_weight, fp_weight, fn_weight) < 0:
        raise ValueError("weighted counts must be non-negative")
    denominator = tp_weight + alpha * fp_weight + beta * fn_weight + epsilon
    return float(tp_weight / denominator)


def compute_dti_components(
    predictions: np.ndarray,
    ground_truth: np.ndarray,
    valid_mask: np.ndarray | None = None,
    *,
    radius_m: float = DEFAULT_RADIUS_M,
    pixel_m: float = DEFAULT_PIXEL_M,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    epsilon: float = DEFAULT_EPSILON,
) -> DTIComponents:
    """Compute exact DTI components on 2D arrays using Euclidean Distance Transform."""
    preds = np.asarray(predictions, dtype=np.float32)
    truth = np.asarray(ground_truth, dtype=bool)

    if preds.shape != truth.shape:
        raise ValueError(f"shape mismatch: preds {preds.shape} != truth {truth.shape}")

    if valid_mask is not None:
        mask = np.asarray(valid_mask, dtype=bool)
        if mask.shape != preds.shape:
            raise ValueError(f"mask shape {mask.shape} != preds {preds.shape}")
        preds = np.where(mask, preds, 0.0)
        truth = truth & mask

    pred_binary = preds > 0.0
    num_truth = float(np.count_nonzero(truth))
    num_pred = float(np.count_nonzero(pred_binary))

    if num_truth == 0.0 and num_pred == 0.0:
        return DTIComponents(tp_weight=0.0, fp_weight=0.0, fn_weight=0.0, score=1.0)
    if num_truth == 0.0:
        return DTIComponents(tp_weight=0.0, fp_weight=num_pred, fn_weight=0.0, score=0.0)
    if num_pred == 0.0:
        return DTIComponents(tp_weight=0.0, fp_weight=0.0, fn_weight=num_truth, score=0.0)

    # 1. Distance transform from predictions to ground truth
    # edt gives distance in pixels; multiply by pixel_m
    dist_to_pred_px = distance_transform_edt(~pred_binary)
    dist_to_pred_m = dist_to_pred_px * pixel_m
    kernel_on_truth = np.maximum(0.0, 1.0 - dist_to_pred_m / radius_m)
    tp_weight = float(np.sum(kernel_on_truth[truth]))

    # 2. Distance transform from truth to predictions (for false positive penalty)
    dist_to_truth_px = distance_transform_edt(~truth)
    dist_to_truth_m = dist_to_truth_px * pixel_m
    # In official evaluation, false positive penalty is weighted by distance to nearest truth
    # If a prediction is within radius_m of truth, it carries reduced FP penalty: (1 - kernel)
    fp_kernel = np.maximum(0.0, 1.0 - dist_to_truth_m / radius_m)
    fp_weight = float(np.sum((1.0 - fp_kernel)[pred_binary]))

    fn_weight = float(max(0.0, num_truth - tp_weight))
    score = dti_from_counts(tp_weight, fp_weight, fn_weight, alpha=alpha, beta=beta, epsilon=epsilon)

    return DTIComponents(tp_weight=tp_weight, fp_weight=fp_weight, fn_weight=fn_weight, score=score)


def compute_dti(
    predictions: np.ndarray,
    ground_truth: np.ndarray,
    valid_mask: np.ndarray | None = None,
    *,
    radius_m: float = DEFAULT_RADIUS_M,
    pixel_m: float = DEFAULT_PIXEL_M,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
) -> float:
    """Return the scalar Distance-Weighted Tversky score."""
    return compute_dti_components(
        predictions,
        ground_truth,
        valid_mask,
        radius_m=radius_m,
        pixel_m=pixel_m,
        alpha=alpha,
        beta=beta,
    ).score
