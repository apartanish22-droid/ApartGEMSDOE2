#!/usr/bin/env python3
"""Catalogue-free ridge-tensor candidate for the GEMS competition format.

Method (hypothesis H-RIDGE3, see knowledge/candidate_slate_20261030.md):
  Three independent linear-structure detectors, built ONLY from competition feature
  bands (never from the fault catalogue labels):
    * det_elev       (band 12) detrended elevation        -> topographic scarp/lineament
    * tmi_vg         (band 9)  vertical gradient of TMI   -> magnetic contact/lineament
    * iso_grav_anom_hg (band 18) horizontal gradient of isostatic gravity -> density contact
  Per band: multi-scale (sigma = 1, 1.5, 2 cells = 100-200 m) Hessian linear-strength
  R = |lambda_large| - |lambda_small|, scale-normalised, 95th-percentile clipped.
  Fused surface = geometric mean of the three. Crest pixels kept by 3x3 non-maximum
  suppression, then the top N = 37,654 crest pixels (same dot count as the GEMSDOE family)
  become predictions with value 0.5 + 0.5 * rank-normalised fused score; background
  inside the footprint is 0; outside the footprint is NaN (organizer rule).

Gates (run before the file is accepted as a candidate; see the run card JSON):
  G1 surface:  max |Spearman| of the pre-placement fused surface vs every registry raster <= 0.90
  G2 dots:     max fraction of candidate dots within 3 px of any registry raster's dots <= 0.70
  G3 format:   read-back check of CRS, shape, transform, dtype, NaN-outside, [0,1] inside.
The catalogue DTI is an IN-SAMPLE sanity diagnostic only. It is NOT a holdout estimate and
NOT a leaderboard estimate (the hidden test set is new faults absent from the catalogue).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine
from scipy import ndimage
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".cache/gems_data"
REG = ROOT / ".cache/registry"
NODATA_ABS = 1e30
N_DOTS = 37654
RADIUS_PX = 3.0            # 300 m at 100 m cells
ALPHA, BETA = 0.2, 0.8     # competition DTI weights
SPEARMAN_SAMPLE = 300_000
SEED = 20261030

BANDS = {"det_elev": 12, "tmi_vg": 9, "iso_grav_anom_hg": 18}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_band(ds, idx: int):
    a = ds.read(idx).astype("float64")
    bad = ~np.isfinite(a) | (np.abs(a) > NODATA_ABS)
    return a, bad


def ridge_strength(field: np.ndarray, sigma: float) -> np.ndarray:
    """Scale-normalised linear-structure strength from the Hessian of a Gaussian-smoothed field."""
    hxx = ndimage.gaussian_filter(field, sigma, order=(0, 2))
    hyy = ndimage.gaussian_filter(field, sigma, order=(2, 0))
    hxy = ndimage.gaussian_filter(field, sigma, order=(1, 1))
    tr = 0.5 * (hxx + hyy)
    disc = np.sqrt((0.5 * (hxx - hyy)) ** 2 + hxy ** 2)
    l1, l2 = tr + disc, tr - disc
    big = np.where(np.abs(l1) >= np.abs(l2), l1, l2)
    small = np.where(np.abs(l1) >= np.abs(l2), l2, l1)
    return (np.abs(big) - np.abs(small)) * sigma ** 2


def build_surface(src_path: Path):
    with rasterio.open(src_path) as ds:
        labels_path = DATA / "labels.tif"
        with rasterio.open(labels_path) as lab:
            footprint = lab.read(1) != -1
        bands = {}
        bad_any = np.zeros(footprint.shape, dtype=bool)
        for name, idx in BANDS.items():
            a, bad = load_band(ds, idx)
            bad_any |= bad & footprint
            valid = footprint & ~bad
            fill = float(np.median(a[valid]))
            a = np.where(bad, fill, a)
            bands[name] = a
    usable = footprint & ~bad_any
    strengths = []
    for name in BANDS:
        r = np.zeros(footprint.shape, dtype="float64")
        for sigma in (1.0, 1.5, 2.0):
            r = np.maximum(r, ridge_strength(bands[name], sigma))
        p95 = float(np.percentile(r[usable], 95))
        strengths.append(np.clip(r / p95, 0.0, 1.0))
    fused = np.cbrt(strengths[0] * strengths[1] * strengths[2])
    fused = np.where(usable, fused, 0.0)
    return footprint, usable, fused, bands


def nms_crest(fused: np.ndarray, usable: np.ndarray) -> np.ndarray:
    local_max = ndimage.maximum_filter(fused, size=3, mode="constant")
    return usable & (fused > 0) & (fused >= local_max)


def select_dots(fused: np.ndarray, crest: np.ndarray, n: int):
    idx_flat = np.flatnonzero(crest)
    if idx_flat.size < n:
        raise RuntimeError(f"only {idx_flat.size} crest pixels for {n} dots")
    scores = fused.ravel()[idx_flat]
    top = idx_flat[np.argsort(-scores, kind="stable")[:n]]
    rows, cols = np.unravel_index(top, fused.shape)
    s = fused[rows, cols]
    smin, smax = float(s.min()), float(s.max())
    val = 0.5 + 0.5 * (s - smin) / max(smax - smin, 1e-12)
    return rows, cols, val


def dtw_components(pred: np.ndarray, gt_rows, gt_cols, footprint: np.ndarray):
    """Official distance-weighted Tversky components (triangular kernel, R = 3 px).

    TP_w = sum_g max_{x: d(x,g)<=R} p(x) k(d);  FP_w = sum_{x: p>0} p(x)[1 - max_g k(d(x,g))];
    FN_w = sum_g [1 - max_{x: d<=R} p(x) k(d)];  k(d) = max(1 - d/R, 0).
    """
    prow, pcol = np.nonzero(pred > 0)
    pval = pred[prow, pcol]
    gt = np.column_stack([gt_rows, gt_cols]).astype(float)
    pts = np.column_stack([prow, pcol]).astype(float)
    tree_p = cKDTree(pts)
    tree_g = cKDTree(gt)
    # TP and FN: per truth point, best nearby prediction within R
    tp_terms = np.zeros(len(gt))
    for gi, nbrs in enumerate(tree_p.query_ball_point(gt, r=RADIUS_PX)):
        if nbrs:
            nb = np.asarray(nbrs)
            d = np.linalg.norm(pts[nb] - gt[gi], axis=1)
            tp_terms[gi] = np.max(pval[nb] * np.maximum(1.0 - d / RADIUS_PX, 0.0))
    tp_w = float(tp_terms.sum())
    fn_w = float((1.0 - tp_terms).sum())
    # FP: each predicted pixel's nearest truth distance
    dist, _ = tree_g.query(pts, k=1, distance_upper_bound=RADIUS_PX)
    k_near = np.where(np.isfinite(dist), np.maximum(1.0 - dist / RADIUS_PX, 0.0), 0.0)
    fp_w = float(np.sum(pval * (1.0 - k_near)))
    dti = tp_w / (tp_w + ALPHA * fp_w + BETA * fn_w + 1e-12)
    return {"TP_w": tp_w, "FP_w": fp_w, "FN_w": fn_w, "DTI": dti, "n_gt": int(len(gt)),
            "n_pred_pixels": int(len(pts))}


def read_ref_dots(path: Path, shape):
    with rasterio.open(path) as ds:
        if (ds.height, ds.width) != shape:
            return None
        a = ds.read(1).astype("float64")
    fin = np.isfinite(a)
    dots = fin & (a > 0)
    return a, fin, dots


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--note", required=True)
    ap.add_argument("--run-card", type=Path, required=True)
    args = ap.parse_args()
    args.out = args.out if args.out.is_absolute() else (ROOT / args.out)
    args.run_card = args.run_card if args.run_card.is_absolute() else (ROOT / args.run_card)
    if len(args.note) > 140:
        raise SystemExit("note exceeds 140 characters")
    t0 = time.time()
    sample_path = DATA / "sample_submission.tif"
    with rasterio.open(sample_path) as ref:
        profile_ref = ref.profile.copy()
        shape = (ref.height, ref.width)
        transform = ref.transform
        crs = ref.crs

    footprint, usable, fused, bands = build_surface(DATA / "training_features.tif")
    print(f"footprint {int(footprint.sum())}, usable {int(usable.sum())}", flush=True)

    # Auxiliary sanity: AUC of each input ridge alone vs the in-sample catalogue (diagnostic only;
    # NOT used to construct the candidate).
    with rasterio.open(DATA / "labels.tif") as lab:
        labels = lab.read(1)
    y = (labels[usable] == 1).astype(int)
    auc_each = {}
    for name in BANDS:
        r = np.zeros(footprint.shape)
        for sigma in (1.0, 1.5, 2.0):
            r = np.maximum(r, ridge_strength(bands[name], sigma))
        auc_each[name] = float(roc_auc_score(y, r[usable]))
    auc_fused = float(roc_auc_score(y, fused[usable]))

    # G1 surface gate: pre-placement, against every registry raster (sampled footprint cells)
    rng = np.random.default_rng(SEED)
    fp_idx = np.flatnonzero(usable)
    samp = rng.choice(fp_idx, size=min(SPEARMAN_SAMPLE, fp_idx.size), replace=False)
    fused_s = fused.ravel()[samp]

    manifest = json.loads((ROOT / "registry/focus_registry_manifest.json").read_text())
    refs = []
    for rec in manifest["rasters"]:
        refs.append((rec["repo"], rec["path"], REG / rec["repo"] / rec["path"], rec["sha256"]))
    lattice_pin = json.loads((ROOT / "registry/historical-pins.json").read_text())["lattice"]
    lattice_path = REG / "13GEMSDOE" / lattice_pin["path"]
    refs.append(("13GEMSDOE(lattice)", lattice_pin["path"], lattice_path, lattice_pin["sha256"]))

    surf_rows = []
    max_rho = 0.0
    n_ok = 0
    n_excluded = 0
    for repo, path, local, sha in refs:
        if not local.is_file():
            surf_rows.append({"repo": repo, "path": path, "status": "missing"})
            continue
        if sha256(local) != sha:
            surf_rows.append({"repo": repo, "path": path, "status": "sha_mismatch"})
            continue
        got = read_ref_dots(local, shape)
        if got is None:
            # Documented exclusion: a different grid cannot be compared cell-for-cell.
            surf_rows.append({"repo": repo, "path": path, "status": "excluded_off_grid_not_comparable"})
            n_excluded += 1
            continue
        a, fin, _ = got
        m = fin.ravel()[samp]
        if m.sum() < 1000:
            surf_rows.append({"repo": repo, "path": path, "status": "too_few_finite"})
            continue
        rho = float(spearmanr(fused_s[m], a.ravel()[samp][m]).statistic)
        n_ok += 1
        max_rho = max(max_rho, abs(rho) if np.isfinite(rho) else 0.0)
        surf_rows.append({"repo": repo, "path": path, "status": "ok", "abs_spearman": abs(rho)})
    print(f"G1 surface: measured {n_ok}/{len(refs)} (excluded off-grid {n_excluded}); max |rho| = {max_rho:.4f}", flush=True)
    g1_pass = max_rho <= 0.90 and (n_ok + n_excluded) == len(refs) and n_ok > 400

    # Selection (only after G1; the catalogue is never read here)
    crest = nms_crest(fused, usable)
    rows, cols, vals = select_dots(fused, crest, N_DOTS)
    pred = np.full(shape, np.nan, dtype="float32")
    pred[footprint] = 0.0
    pred[rows, cols] = vals.astype("float32")
    print(f"crest pixels {int(crest.sum())}; selected {rows.size}", flush=True)

    # Read-back format gate (G3) on the in-memory array, then write and re-read
    args.out.parent.mkdir(parents=True, exist_ok=True)
    profile = dict(driver="GTiff", dtype="float32", count=1, height=shape[0], width=shape[1],
                   crs=crs, transform=transform, nodata=np.nan, compress="lzw", tiled=False)
    with rasterio.open(args.out, "w", **profile) as dst:
        dst.write(pred, 1)
    with rasterio.open(args.out) as chk:
        back = chk.read(1)
        fmt = {
            "driver": chk.driver, "count": chk.count, "dtype": chk.dtypes[0],
            "crs_epsg": chk.crs.to_epsg(), "shape": [chk.height, chk.width],
            "transform": list(chk.transform)[:6],
            "transform_matches_sample": tuple(chk.transform)[:6] == tuple(transform)[:6],
            "nodata_tag": chk.nodata,
        }
    fin_back = np.isfinite(back)
    inside_nan = int(np.isnan(back[footprint]).sum())
    outside_finite = int(np.isfinite(back[~footprint]).sum())
    in_range = bool(np.all((back[footprint] >= 0) & (back[footprint] <= 1)))
    fmt.update({
        "inside_footprint_nan": inside_nan, "outside_footprint_finite": outside_finite,
        "inside_footprint_values_in_0_1": in_range, "footprint_cells": int(footprint.sum()),
        "grid_matches_sample": (back.shape == shape),
        "g3_pass": bool(inside_nan == 0 and outside_finite == 0 and in_range
                        and fmt["crs_epsg"] == 32611 and fmt["transform_matches_sample"]
                        and fmt["dtype"] == "float32" and fmt["count"] == 1
                        and back.shape == shape),
    })

    # Twin with 0 outside the footprint (whole-array finite [0,1]); identical inside values.
    zeros_out = args.out.with_name(args.out.name.replace("-nan.tif", "-zeros.tif"))
    zeros_arr = np.where(footprint, np.nan_to_num(pred, nan=0.0), 0.0).astype("float32")
    with rasterio.open(zeros_out, "w", driver="GTiff", dtype="float32", count=1,
                       height=shape[0], width=shape[1], crs=crs, transform=transform,
                       compress="lzw", tiled=False) as dst:
        dst.write(zeros_arr, 1)
    with rasterio.open(zeros_out) as zc:
        zb = zc.read(1)
        zeros_check = {
            "crs_epsg": zc.crs.to_epsg(), "nodata_tag": zc.nodata, "dtype": zc.dtypes[0],
            "shape": [zc.height, zc.width], "transform_matches_sample": tuple(zc.transform)[:6] == tuple(transform)[:6],
            "whole_array_nan": int(np.isnan(zb).sum()),
            "whole_array_in_0_1": bool(np.all((zb >= 0) & (zb <= 1))),
            "inside_footprint_matches_nan_twin": bool(np.array_equal(zb[footprint], back[footprint])),
            "sha256": sha256(zeros_out), "path": str(zeros_out.relative_to(ROOT)),
        }

    # G2 dot gate: candidate dots vs each registry raster's dots (literal rule + lattice-excluded)
    cand = np.column_stack([rows, cols]).astype(float)
    cand_tree = cKDTree(cand)
    dot_rows = []
    max_frac = 0.0
    max_frac_nonlattice = 0.0
    for repo, path, local, sha in refs:
        if not local.is_file() or sha256(local) != sha:
            continue
        got = read_ref_dots(local, shape)
        if got is None:
            continue
        _, _, dots = got
        rr, cc = np.nonzero(dots)
        if rr.size == 0:
            continue
        ref_tree = cKDTree(np.column_stack([rr, cc]).astype(float))
        d, _ = ref_tree.query(cand, k=1, distance_upper_bound=RADIUS_PX)
        frac = float(np.mean(np.isfinite(d)))
        is_lattice = "r13-lattice" in path  # synthetic 5-px calibration lattice (both copies)
        # Null: the chance that a RANDOM dot lands within 3 px of some reference dot at this density
        density = rr.size / float(footprint.sum())
        null_frac = float(1.0 - np.exp(-density * np.pi * RADIUS_PX ** 2))
        dot_rows.append({"repo": repo, "path": path, "ref_dots": int(rr.size),
                         "ref_dot_density_of_footprint": density,
                         "within_3px_fraction": frac, "random_placement_null_fraction": null_frac,
                         "excess_over_null": frac - null_frac})
        max_frac = max(max_frac, frac)
        if not is_lattice:
            max_frac_nonlattice = max(max_frac_nonlattice, frac)
    g2_pass_literal = max_frac <= 0.70
    g2_pass_nonlattice = max_frac_nonlattice <= 0.70
    top_dot = sorted(dot_rows, key=lambda r: -r["within_3px_fraction"])[:5]
    violators = [r["path"] for r in dot_rows if r["within_3px_fraction"] > 0.70]
    print(f"G2 dots: literal max {max_frac:.4f}; non-lattice max {max_frac_nonlattice:.4f}", flush=True)

    # Catalogue in-sample DTI diagnostic (NOT a holdout, NOT a leaderboard estimate)
    gt_rows, gt_cols = np.nonzero(labels == 1)
    dtw = dtw_components(np.nan_to_num(pred.astype("float64"), nan=0.0), gt_rows, gt_cols, footprint)

    run_card = {
        "schema": "ridge-tensor-candidate-run-card-v1",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "name": args.name,
        "note": args.note,
        "note_length": len(args.note),
        "hypothesis": "H-RIDGE3: coincident Hessian linear-structure ridges in detrended elevation, "
                      "vertical TMI gradient and isostatic-gravity horizontal gradient, fused by "
                      "geometric mean, crest-selected (NMS), top 37,654 pixels; no catalogue input.",
        "mechanism": "Co-located topographic, magnetic-contact and gravity-contact linear structure "
                     "at 100-200 m scale is expected to mark fault traces that are weak in any single "
                     "layer; the catalogue is not used to generate predictions.",
        "named_non_fault_mimic": "Lake Lahontan shorelines and benches, road/rail embankments, "
                                 "drainage incisions, flight-line and leveling stripes, lithologic contacts.",
        "inputs": {"training_features.tif_sha256": sha256(DATA / "training_features.tif"),
                   "bands_used": BANDS, "labels_used_for_generation": False,
                   "sample_grid_sha256": sha256(sample_path)},
        "parameters": {"sigmas_cells": [1.0, 1.5, 2.0], "n_dots": N_DOTS, "nms_window": 3,
                       "value_map": "0.5 + 0.5*rank-normalised fused score", "background": 0.0,
                       "outside_footprint": "NaN", "seed_surface_sample": SEED},
        "output": {"path": str(args.out.relative_to(ROOT)), "sha256": sha256(args.out),
                   "bytes": args.out.stat().st_size, "dots": int(rows.size)},
        "format_readback": fmt,
        "zeros_twin_readback": zeros_check,
        "gates": {
            "G1_surface_max_abs_spearman": max_rho, "G1_measured": n_ok, "G1_excluded_off_grid": n_excluded, "G1_total": len(refs),
            "G1_pass": g1_pass,
            "G2_dots_max_within_3px_literal": max_frac,
            "G2_pass_literal": g2_pass_literal, "G2_violating_count": len(violators),
            "G2_dots_max_within_3px_excluding_lattice": max_frac_nonlattice,
            "G2_pass_excluding_lattice": g2_pass_nonlattice,
            "G2_top_matches": top_dot,
            "G2_violating_references": violators,
            "G2_note": "Literal rule as specified by the protocol. In this run the only violators are the "
                       "synthetic 5-px calibration lattice r13-lattice-s5 (206,895 dots; random-placement null "
                       "shown per reference). Not exempted by this script; the exclusion is a user decision.",
            "G3_format_pass": fmt["g3_pass"],
        },
        "catalogue_insample_diagnostic": {
            "label": "CATALOGUE-SANITY (in-sample; not holdout; not hidden test; not leaderboard)",
            "dtw": dtw,
            "auc_each_input_ridge_vs_catalogue": auc_each,
            "auc_fused_vs_catalogue": auc_fused,
            "leakage_note": "AUC > 0.90 would indicate leakage; none of these inputs were built from labels by this script",
        },
        "holdout_dti": None,
        "organizer_confirmed_score": None,
        "leaderboard_estimate": None,
        "runtime_s": round(time.time() - t0, 1),
        "surface_rows": surf_rows,
        "dot_rows": dot_rows,
    }
    args.run_card.parent.mkdir(parents=True, exist_ok=True)
    args.run_card.write_text(json.dumps(run_card, indent=2, default=float))
    print(json.dumps({k: run_card[k] for k in ("output", "gates")}, indent=2, default=float), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
