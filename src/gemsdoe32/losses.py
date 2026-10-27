"""Metric-shaped loss functions matching the GEMS 300 m distance geometry."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt


class MetricShapedBoundaryLoss:
    """Boundary loss (Kervadec et al., 2018) parameterized by the 300 m competition kernel.

    Instead of penalizing exact pixel mismatches equally, it computes the distance
    transform phi_G to ground truth contours, rewarding predictions that land within
    the 300 m support radius.
    """

    def __init__(self, radius_m: float = 300.0, pixel_m: float = 100.0):
        self.radius_m = float(radius_m)
        self.pixel_m = float(pixel_m)
        self.radius_px = self.radius_m / self.pixel_m

    def compute_distance_weight_map(self, ground_truth: np.ndarray) -> np.ndarray:
        """Compute the signed/distance map phi_G(x) in meters, capped at radius_m."""
        truth = np.asarray(ground_truth, dtype=bool)
        if not np.any(truth):
            return np.ones_like(truth, dtype=np.float32) * self.radius_m

        dist_out_px = distance_transform_edt(~truth)
        dist_out_m = dist_out_px * self.pixel_m

        # Outside distance transformed into normalized linear penalty [0, 1]
        weight_map = np.clip(dist_out_m / self.radius_m, 0.0, 1.0)
        # Inside ground truth pixels get negative weight (reward)
        weight_map[truth] = -1.0
        return weight_map.astype(np.float32)

    def __call__(self, predicted_probs: np.ndarray, ground_truth: np.ndarray) -> float:
        """Calculate the scalar boundary loss."""
        preds = np.asarray(predicted_probs, dtype=np.float32)
        weight_map = self.compute_distance_weight_map(ground_truth)
        loss = float(np.mean(preds * weight_map))
        return loss


class CombinedTverskyBoundaryLoss:
    """Hybrid loss combining regional Distance-Weighted Tversky and Boundary loss."""

    def __init__(
        self,
        alpha: float = 0.2,
        beta: float = 0.8,
        boundary_weight: float = 0.3,
        radius_m: float = 300.0,
    ):
        self.alpha = float(alpha)
        self.beta = float(beta)
        self.boundary_weight = float(boundary_weight)
        self.boundary_loss = MetricShapedBoundaryLoss(radius_m=radius_m)

    def __call__(self, predicted_probs: np.ndarray, ground_truth: np.ndarray) -> float:
        preds = np.asarray(predicted_probs, dtype=np.float32)
        truth = np.asarray(ground_truth, dtype=bool)

        tp = np.sum(preds * truth)
        fp = np.sum(preds * (~truth))
        fn = np.sum((1.0 - preds) * truth)

        tversky_index = (tp + 1e-6) / (tp + self.alpha * fp + self.beta * fn + 1e-6)
        tversky_loss = 1.0 - tversky_index

        b_loss = self.boundary_loss(preds, truth)
        total_loss = float(tversky_loss + self.boundary_weight * b_loss)
        return total_loss
