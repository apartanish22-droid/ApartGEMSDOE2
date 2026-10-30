#!/usr/bin/env python3
"""Label-free ridge-consensus candidate for the GEMS Prize (v4 protocol).

Method (one lane, three pre-declared experiments; see docs/research/v4-ridge-experiments.md):

  * Inputs: ONLY the competition feature stack (training_features.tif, 19 bands).
    The catalogue labels are used ONLY for scoring, never for building a feature
    or choosing a candidate pixel. Therefore no catalogue-derived feature exists
    that could leak, and the hide-and-recover split reduces to scoring on withheld
    spatial blocks.
  * Score field: magnetic horizontal gradient (tmi_hg, band 3) and optionally the
    isostatic-gravity horizontal gradient (iso_grav_anom_hg, band 18), each z-scored
    on the footprint.
  * Ridge: Canny-style non-maximum suppression of the score ALONG the normal of the
    smoothed TMI field (band 14). A pixel survives only if it is a local maximum
    across the lineament direction.
  * Selection: the top q fraction (of the footprint) of surviving ridge pixels.
  * Output: float32 raster, finite in [0,1] inside the footprint, NaN outside it
    (the sample_submission convention), same grid as sample_submission.tif.

Scoring uses the exact distance-weighted Tversky index in src/gems32/metric.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32 import metric  # noqa: E402  (official DTI, alpha=0.2 beta=0.8 R=3 px)

DATA = ROOT / ".cache" / "gems_data"
BAND = {"tmi": 14, "tmi_hg": 3, "iso_grav_anom_hg": 18}


def load_footprint() -> np.ndarray:
    with rasterio.open(DATA / "labels.tif") as src:
        return src.read(1) != -1


def load_labels() -> np.ndarray:
    with rasterio.open(DATA / "labels.tif") as src:
        return src.read(1) == 1


def load_band(index: int, footprint: np.ndarray) -> np.ndarray:
    """Band as float64, non-finite / nodata cells set to NaN, then z-scored on the footprint."""
    with rasterio.open(DATA / "training_features.tif") as src:
        a = src.read(index).astype(np.float64)
        nodata = src.nodata
    bad = ~np.isfinite(a)
    if nodata is not None:
        bad |= a == nodata
    a[bad] = np.nan
    valid = footprint & np.isfinite(a)
    mu, sd = a[valid].mean(), a[valid].std()
    z = (a - mu) / sd
    z[~np.isfinite(z)] = 0.0  # neutral score where the feature is missing
    return z


def normal_direction(tmi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    smooth = ndi.gaussian_filter(np.where(np.isfinite(tmi), tmi, 0.0), 1.0)
    gy, gx = np.gradient(smooth)
    norm = np.hypot(gx, gy) + 1e-12
    return gy / norm, gx / norm


def nms_across_normal(score: np.ndarray, ny: np.ndarray, nx: np.ndarray) -> np.ndarray:
    """Keep pixels that are >= the bilinear-sampled score one pixel either side along the normal."""
    yy, xx = np.indices(score.shape, dtype=np.float64)
    keep = np.ones(score.shape, bool)
    for t in (-1.0, 1.0):
        sy = np.clip(yy + t * ny, 0, score.shape[0] - 1)
        sx = np.clip(xx + t * nx, 0, score.shape[1] - 1)
        neigh = ndi.map_coordinates(score, [sy, sx], order=1, mode="nearest")
        keep &= score >= neigh
    return keep


def select_top_fraction(score: np.ndarray, ridge: np.ndarray, footprint: np.ndarray,
                        tune_mask: np.ndarray, q: float) -> np.ndarray:
    """Binary selection: ridge pixels whose score is in the top q of footprint ridge pixels (tuning half)."""
    pool = ridge & tune_mask
    n_keep = int(round(q * tune_mask.sum()))
    if pool.sum() == 0 or n_keep == 0:
        return np.zeros_like(ridge)
    cut = np.partition(score[pool], -min(n_keep, pool.sum()))[-min(n_keep, pool.sum())]
    return ridge & (score >= cut) & footprint


def build_prediction(score: np.ndarray, ridge: np.ndarray, footprint: np.ndarray,
                     tune_mask: np.ndarray, q: float, dilate: bool) -> np.ndarray:
    sel = select_top_fraction(score, ridge, footprint, tune_mask, q)
    p = sel.astype(np.float32)
    if dilate:
        ring = ndi.binary_dilation(sel, structure=np.ones((3, 3), bool)) & ~sel & footprint
        p[ring] = 0.5
    p[~footprint] = 0.0
    return p


def score_region(pred: np.ndarray, truth: np.ndarray, region: np.ndarray) -> dict:
    comp = metric.components(pred, truth, valid=region)
    dti = metric.dti(comp["TP_w"], comp["FP_w"], comp["FN_w"])
    return {**comp, "DTI": dti, "n_truth": int((truth & region).sum())}


def finalize_output(pred: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    out = np.where(footprint, np.clip(pred, 0.0, 1.0), np.nan).astype(np.float32)
    return out


def write_tif(path: Path, data: np.ndarray) -> None:
    with rasterio.open(DATA / "sample_submission.tif") as ref:
        profile = ref.profile.copy()
        profile.update(dtype="float32", count=1, nodata=np.nan, compress="deflate", tiled=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data.astype(np.float32), 1)
