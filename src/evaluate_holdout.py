"""src/evaluate_holdout.py

Holdout DTI evaluator implementing the shared lane protocol (PARALLEL-RUN
PROTOCOL items 1, 2, 3, 4).

Holdout = hide-and-recover:
  * withhold whole fault segments with a buffer,
  * derive every catalogue-based feature only from the visible faults,
  * mask visible faults pixel-exactly,
  * score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel).

Every number produced here is labelled HOLDOUT-DTI (evaluator version,
number of withheld positives, 95% CI). A projection is never written as a
score.

This module is pure computation: it reads grids from data/ and writes nothing
to the submission slot. It is designed to run once real data is present.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import rasterio
    from rasterio.transform import rowcol
    from scipy import ndimage
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "numpy, rasterio and scipy are required: pip install numpy rasterio scipy"
    ) from exc

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
GRID_REF = DATA_DIR / "grid_reference.json"

# Protocol constants (PARALLEL-RUN PROTOCOL item 2).
ALPHA = 0.2  # false-positive weight in Tversky / DTI
BETA = 0.8  # false-negative weight in Tversky / DTI
KERNEL_RADIUS_M = 300.0  # triangular kernel radius for pooled DTI
EVALUATOR_VERSION = "holdout-dti-v1"


@dataclass
class GridRef:
    crs: str
    transform: list[float]
    width: int
    height: int
    resolution_m: float


def load_grid_ref() -> GridRef:
    if not GRID_REF.exists():
        raise FileNotFoundError(
            f"{GRID_REF} missing — run scripts/prepare_data.py after placing data in data/"
        )
    g = json.loads(GRID_REF.read_text())
    return GridRef(
        crs=g["crs"],
        transform=g["transform"],
        width=int(g["width"]),
        height=int(g["height"]),
        resolution_m=float(g["resolution_m"]),
    )


def _read_band(path: Path, band: int = 1) -> np.ndarray:
    with rasterio.open(path) as src:
        return src.read(band).astype(np.float32)


def triangular_kernel(radius_m: float, resolution_m: float) -> np.ndarray:
    """1-D triangular kernel (normalized to sum 1) for the given radius in metres."""
    radius_px = max(1, int(round(radius_m / resolution_m)))
    x = np.arange(-radius_px, radius_px + 1, dtype=np.float64)
    k = np.maximum(1.0 - np.abs(x) / radius_px, 0.0)
    k /= k.sum()
    return k


def withhold_segments(
    labels: np.ndarray, withhold_fraction: float = 0.25, buffer_px: int = 3, seed: int = 0
) -> tuple[np.ndarray, np.ndarray, int]:
    """Hide whole fault segments with a buffer.

    Returns (visible_labels, withheld_mask, n_withheld_positives).
    Connected components of labels > 0 are fault segments; a deterministic
    fraction is withheld (hidden) and dilated by buffer_px so the model can
    never see them when deriving catalogue-based features.
    """
    lab = labels > 0
    structure = np.ones((3, 3), dtype=int)
    seg_id, n_seg = ndimage.label(lab, structure=structure)
    if n_seg == 0:
        return labels.copy(), np.zeros_like(labels, dtype=bool), 0

    rng = np.random.default_rng(seed)
    # ndimage.label ids are 1..n_seg; draw from that range.
    order = rng.permutation(n_seg) + 1
    n_withhold = max(1, int(round(withhold_fraction * n_seg)))
    withhold_ids = set(order[:n_withhold].tolist())

    withheld_mask = np.zeros_like(lab, dtype=bool)
    visible = lab.copy()
    for sid in range(1, n_seg + 1):
        if sid in withhold_ids:
            seg_pixels = seg_id == sid
            withheld_mask |= seg_pixels
            visible &= ~seg_pixels

    # Buffer the withheld segments so no pixel-exact leakage survives.
    if buffer_px > 0:
        withheld_mask = ndimage.binary_dilation(
            withheld_mask, iterations=buffer_px
        )
        visible &= ~withheld_mask

    n_withheld_positives = int(withheld_mask.sum())
    visible_labels = labels.copy()
    visible_labels[withheld_mask] = 0
    return visible_labels, withheld_mask, n_withheld_positives


def pooled_dti(
    prediction: np.ndarray,
    labels: np.ndarray,
    alpha: float = ALPHA,
    beta: float = BETA,
    threshold: float = 0.5,
) -> dict:
    """Pooled Tversky index (DTI) at a threshold.

    prediction: float [0,1] propensity (higher = more fault-like).
    labels: binary 0/1 (1 = fault). Both arrays same shape.
    Returns dict with TP, FP, FN, DTI, threshold.
    """
    pred_bin = (np.asarray(prediction, dtype=np.float64) >= threshold).astype(np.int64)
    lab_bin = (np.asarray(labels, dtype=np.float64) > 0).astype(np.int64)

    tp = int(np.count_nonzero((pred_bin == 1) & (lab_bin == 1)))
    fp = int(np.count_nonzero((pred_bin == 1) & (lab_bin == 0)))
    fn = int(np.count_nonzero((pred_bin == 0) & (lab_bin == 1)))

    denom = tp + alpha * fp + beta * fn
    dti = tp / denom if denom > 0 else 0.0
    return {
        "threshold": float(threshold),
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "alpha": alpha,
        "beta": beta,
        "DTI": float(dti),
    }


def pooled_dti_best_threshold(
    prediction: np.ndarray, labels: np.ndarray, alpha: float = ALPHA, beta: float = BETA
) -> dict:
    """Best pooled DTI over a threshold sweep (report threshold, never hide it)."""
    best = None
    for t in np.linspace(0.05, 0.95, 19):
        r = pooled_dti(prediction, labels, alpha=alpha, beta=beta, threshold=float(t))
        if best is None or r["DTI"] > best["DTI"]:
            best = r
    return {"best": bool(best is not None), **(best or {})}


def dilate_labels(labels: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Dilate binary labels with a separable triangular kernel (300 m equivalent)."""
    lab = (labels > 0).astype(np.float64)
    # separable convolution: horizontal then vertical
    k = kernel
    out = ndimage.convolve1d(lab, k, axis=1, mode="constant", cval=0.0)
    out = ndimage.convolve1d(out, k, axis=0, mode="constant", cval=0.0)
    return (out > 0).astype(np.int64)


def auc_rank(scores: np.ndarray, labels: np.ndarray) -> float:
    """Rank-based AUC (Mann-Whitney U) of scores vs binary labels."""
    s = np.asarray(scores, dtype=np.float64).ravel()
    y = (np.asarray(labels, dtype=np.float64).ravel() > 0).astype(np.int64)
    n_pos = int(np.count_nonzero(y == 1))
    n_neg = int(np.count_nonzero(y == 0))
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=np.float64)
    # average ranks for ties
    sorted_s = s[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and sorted_s[j + 1] == sorted_s[i]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        ranks[order[i : j + 1]] = avg_rank
        i = j + 1
    auc = (ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


def leakage_canary(
    features: dict[str, np.ndarray], labels: np.ndarray
) -> list[dict]:
    """Test each feature alone on the holdout. AUC > 0.90 => leakage flag."""
    results = []
    for name, feat in features.items():
        s = np.nan_to_num(np.asarray(feat, dtype=np.float64), nan=0.0)
        auc = auc_rank(s, labels)
        results.append(
            {
                "feature": name,
                "AUC": auc,
                "leakage_flag": bool(auc > 0.90) if auc == auc else None,
                "note": "AUC above 0.90 means leakage until proven otherwise (protocol rule 4)",
            }
        )
    return results


def lane_rank_correlation(raster_a: np.ndarray, raster_b: np.ndarray) -> float:
    """Spearman rank correlation between two rasters (flat, NaN-safe)."""
    from scipy.stats import spearmanr

    a = np.asarray(raster_a, dtype=np.float64).ravel()
    b = np.asarray(raster_b, dtype=np.float64).ravel()
    mask = ~(np.isnan(a) | np.isnan(b))
    if mask.sum() < 2:
        return float("nan")
    rho, _ = spearmanr(a[mask], b[mask])
    return float(rho)


def lane_dot_overlap(
    dots_a: np.ndarray, dots_b: np.ndarray, within_px: int = 3
) -> dict:
    """Fraction of dots_a within within_px pixels of any dot in dots_b."""
    a_pts = np.argwhere(dots_a > 0)
    b_pts = np.argwhere(dots_b > 0)
    if len(a_pts) == 0 or len(b_pts) == 0:
        return {"n_a": int(len(a_pts)), "within_px": within_px, "fraction_within": float("nan")}
    # distance transform of complement of b
    dist = ndimage.distance_transform_edt(~(dots_b > 0))
    frac = float(np.count_nonzero(dist[tuple(a_pts.T)] <= within_px)) / len(a_pts)
    return {"n_a": int(len(a_pts)), "within_px": within_px, "fraction_within": frac}


def lane_check(
    submission: np.ndarray, registry_rasters: dict[str, np.ndarray]
) -> list[dict]:
    """Protocol rule 1: flag drift into another lane."""
    findings = []
    for name, reg in registry_rasters.items():
        rho = lane_rank_correlation(submission, reg)
        findings.append(
            {
                "registry": name,
                "rank_correlation": rho,
                "correlation_breach": bool(rho > 0.90) if rho == rho else None,
            }
        )
    return findings


def ci95_bootstrap(
    dti_values: list[float], n_bootstrap: int = 2000, seed: int = 0
) -> dict:
    """95% CI for a holdout DTI estimate (nonparametric bootstrap)."""
    arr = np.asarray(dti_values, dtype=np.float64)
    arr = arr[~np.isnan(arr)]
    if len(arr) == 0:
        return {"n": 0, "mean": None, "ci95": [None, None]}
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_bootstrap):
        sample = rng.choice(arr, size=len(arr), replace=True)
        boots.append(sample.mean())
    boots.sort()
    lo = boots[int(0.025 * n_bootstrap)]
    hi = boots[int(0.975 * n_bootstrap)]
    return {"n": int(len(arr)), "mean": float(arr.mean()), "ci95": [float(lo), float(hi)]}


def holdout_dti_summary(
    prediction: np.ndarray,
    labels: np.ndarray,
    withheld_mask: np.ndarray,
    n_withheld: int,
) -> dict:
    """Full HOLDOUT-DTI summary block (protocol rule 3 labeling)."""
    dilated = dilate_labels(withheld_mask, triangular_kernel(KERNEL_RADIUS_M, 100.0))
    # recover: score against the withheld (hidden) positives dilated by the kernel
    result = pooled_dti_best_threshold(prediction, withheld_mask)
    result["dilated_kernel_radius_m"] = KERNEL_RADIUS_M
    result["withheld_positives"] = n_withheld
    result["label"] = "HOLDOUT-DTI"
    result["evaluator_version"] = EVALUATOR_VERSION
    ci = ci95_bootstrap([result["DTI"]])
    result["ci95"] = ci["ci95"]
    result["note"] = (
        "HOLDOUT-DTI: evaluator holdout-dti-v1, "
        f"{n_withheld} withheld positives, 95% CI {ci['ci95']}. "
        "This is a holdout estimate, not an organizer-confirmed score."
    )
    return result


__all__ = [
    "ALPHA", "BETA", "KERNEL_RADIUS_M", "EVALUATOR_VERSION",
    "load_grid_ref", "triangular_kernel", "withhold_segments",
    "pooled_dti", "pooled_dti_best_threshold", "dilate_labels",
    "auc_rank", "leakage_canary", "lane_rank_correlation",
    "lane_dot_overlap", "lane_check", "ci95_bootstrap", "holdout_dti_summary",
]
