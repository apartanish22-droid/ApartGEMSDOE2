"""AP-1 catalogue-free surface: geometric-mean coincidence of percentile ranks.

Components (official 19-band stack, 1-based band numbers verified from raster tags):
  strain  = mean(rank(band8 dilatation), rank(band7 shear), rank(band4 2nd invariant))
  cond_e  = rank(|grad| band17 cond_surf),  base_e = rank(|grad| band15 depth_to_base_surf)
  grav_e  = rank(|grad| band13 iso_grav_anom)
  S_equal = (strain * cond_e * base_e * grav_e) ** 0.25
  S_strain2 (EXP-2 variant) = (strain**2 * cond_e * base_e * grav_e) ** 0.20
No catalogue/label information enters the surface. Sentinel (-3.4e38) / non-finite
cells are filled with the band's footprint median before gradients so filters see
no artificial cliffs; ranks are computed inside the footprint only.
"""
from __future__ import annotations

import numpy as np
import rasterio
from scipy import ndimage

BANDS = {  # name -> 1-based band index in training_features.tif
    "geod_2ndinv": 4, "geod_shearrate": 7, "geod_dilaterate": 8,
    "iso_grav_anom": 13, "depth_to_base_surf": 15, "cond_surf": 17,
}
SIGMA = 1.5  # px Gaussian pre-smoothing for gradient magnitudes


def footprint_and_labels(data_dir):
    import pathlib
    d = pathlib.Path(data_dir)
    with rasterio.open(d / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(d / "labels.tif") as ds:
        labels = (ds.read(1) == 1) & foot
    return foot, labels


def _read_filled(features_path: str, band: int, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(features_path) as ds:
        a = ds.read(band).astype(np.float32)
    valid = np.isfinite(a) & (a > -1e38) & foot
    med = float(np.median(a[valid])) if valid.any() else 0.0
    out = np.where(valid, a, med).astype(np.float32)
    return out


def _rank_in_footprint(values: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Percentile rank in (0,1] inside footprint; 0 outside. Ties: average-rank via argsort."""
    out = np.zeros(values.shape, dtype=np.float32)
    vals = values[foot]
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty(vals.size, dtype=np.float64)
    ranks[order] = (np.arange(vals.size, dtype=np.float64) + 1.0) / vals.size
    out[foot] = ranks.astype(np.float32)
    del vals, order, ranks
    return out


def _grad_mag(a: np.ndarray) -> np.ndarray:
    gy = ndimage.gaussian_filter(a, SIGMA, order=(1, 0), mode="nearest")
    gx = ndimage.gaussian_filter(a, SIGMA, order=(0, 1), mode="nearest")
    return np.hypot(gx, gy).astype(np.float32)


def auc_rank(scores: np.ndarray, labels: np.ndarray, foot: np.ndarray) -> float:
    """Mann-Whitney AUC of scores for labels inside footprint (full-grid, exact)."""
    m = foot
    vals = scores[m].astype(np.float64)
    lab = labels[m]
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty(vals.size, dtype=np.float64)
    ranks[order] = np.arange(1, vals.size + 1, dtype=np.float64)
    # average ranks for ties
    sv = vals[order]
    i = 0
    r_sorted = ranks[order]
    while i < sv.size:
        j = i
        while j + 1 < sv.size and sv[j + 1] == sv[i]:
            j += 1
        if j > i:
            r_sorted[i:j + 1] = r_sorted[i:j + 1].mean()
        i = j + 1
    ranks[order] = r_sorted
    npos = int(lab.sum()); nneg = int(lab.size - npos)
    if npos == 0 or nneg == 0:
        return float("nan")
    return float((ranks[lab].sum() - npos * (npos + 1) / 2.0) / (npos * nneg))


def build_components(features_path: str, foot: np.ndarray) -> dict[str, np.ndarray]:
    raw = {k: _read_filled(features_path, b, foot) for k, b in BANDS.items()}
    comps_raw = {
        "dilatation": raw["geod_dilaterate"],
        "shear": raw["geod_shearrate"],
        "second_invariant": raw["geod_2ndinv"],
        "cond_edge": _grad_mag(raw["cond_surf"]),
        "base_edge": _grad_mag(raw["depth_to_base_surf"]),
        "grav_edge": _grad_mag(raw["iso_grav_anom"]),
    }
    del raw
    ranks = {k: _rank_in_footprint(v, foot) for k, v in comps_raw.items()}
    del comps_raw
    strain = ((ranks["dilatation"].astype(np.float64) + ranks["shear"]
               + ranks["second_invariant"]) / 3.0).astype(np.float32)
    ranks["strain"] = strain
    return ranks


def combine(ranks: dict[str, np.ndarray], variant: str) -> np.ndarray:
    s = np.maximum(ranks["strain"], 1e-6).astype(np.float64)
    c = np.maximum(ranks["cond_edge"], 1e-6)
    b = np.maximum(ranks["base_edge"], 1e-6)
    g = np.maximum(ranks["grav_edge"], 1e-6)
    if variant == "equal":
        out = (s * c * b * g) ** 0.25
    elif variant == "strain2":
        out = (s ** 2 * c * b * g) ** 0.20
    else:
        raise ValueError(variant)
    return out.astype(np.float32)
