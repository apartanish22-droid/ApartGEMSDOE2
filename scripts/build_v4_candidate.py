#!/usr/bin/env python3
"""Emit the frozen v4 candidate (E2: tmi_hg + iso_grav_anom_hg ridge, q=5% of footprint),
validate the saved bytes, and run the uniqueness gate against every registry raster.

Outputs:
  docs/downloads/<NAME>.tif     - the candidate GeoTIFF (float32, NaN outside footprint)
  docs/downloads/<NAME>.json    - byte-level receipt (sha256, validator output, uniqueness)
  evidence/v4_candidate_run_card.json - run card (protocol item 5)
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ridge_candidate_v4 as rc  # noqa: E402

ROOT = rc.ROOT
NAME = "apartgems-v4-ridge-tmi-isohg-nms-q5pct-20261030"
NOTE = "Label-free ridge NMS on tmi_hg+iso_hg, top 5% of footprint. Catalogue proxy only; not organizer-scored. DO NOT SUBMIT."
FROZEN_Q = 0.05
OVERLAP_LIMIT = 0.70
RHO_LIMIT = 0.90
RADIUS_PX = 3.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_tif(path: Path, footprint: np.ndarray) -> dict:
    with rasterio.open(path) as s, rasterio.open(rc.DATA / "sample_submission.tif") as ref:
        a = s.read(1)
        out = {
            "driver": s.driver, "count": s.count, "dtype": s.dtypes[0],
            "crs_matches_sample": s.crs == ref.crs, "crs": s.crs.to_string(),
            "shape_matches_sample": (s.height, s.width) == (ref.height, ref.width),
            "shape": [s.height, s.width],
            "transform_matches_sample": tuple(s.transform) == tuple(ref.transform),
            "transform": list(s.transform)[:6],
            "res": list(s.res),
        }
    inside = a[footprint]
    outside = a[~footprint]
    out["footprint_cells"] = int(footprint.sum())
    out["nan_inside_footprint"] = int(np.isnan(inside).sum())
    out["finite_inside_footprint"] = bool(np.isfinite(inside).all())
    out["min_inside"] = float(inside.min())
    out["max_inside"] = float(inside.max())
    out["in_unit_interval_inside"] = bool((inside >= 0).all() and (inside <= 1).all())
    out["outside_all_nan"] = bool(np.isnan(outside).all())
    out["positive_dots"] = int((inside > 0).sum())
    out["PASS"] = all([
        out["crs_matches_sample"], out["shape_matches_sample"], out["transform_matches_sample"],
        out["dtype"] == "float32", out["count"] == 1, out["nan_inside_footprint"] == 0,
        out["finite_inside_footprint"], out["in_unit_interval_inside"], out["outside_all_nan"],
    ])
    return out


def dots_within(a_dots: np.ndarray, b_dots: np.ndarray) -> float:
    """Fraction of a_dots within RADIUS_PX pixels of any b_dots cell."""
    if b_dots.sum() == 0 or a_dots.sum() == 0:
        return 0.0
    dist = ndi.distance_transform_edt(~b_dots)
    return float((dist[a_dots] <= RADIUS_PX).mean())


def main() -> int:
    fp = rc.load_footprint()
    H, W = fp.shape
    west = fp.copy(); west[:, W // 2:] = False

    hg = rc.load_band(rc.BAND["tmi_hg"], fp)
    iso = rc.load_band(rc.BAND["iso_grav_anom_hg"], fp)
    tmi = rc.load_band(rc.BAND["tmi"], fp)
    ny, nx = rc.normal_direction(tmi)
    del tmi
    score = hg + iso
    ridge = rc.nms_across_normal(score, ny, nx) & fp
    pred = rc.build_prediction(score, ridge, fp, west, FROZEN_Q, dilate=False)
    out_arr = rc.finalize_output(pred, fp)

    dl = ROOT / "docs" / "downloads"
    tif = dl / f"{NAME}.tif"
    rc.write_tif(tif, out_arr)
    tif_sha = sha256(tif)
    validator = validate_tif(tif, fp)

    # ---- Uniqueness gate: dots within 3 px of ANY registry raster, and rank correlation.
    dots = (out_arr > 0) & fp
    uniq = {}
    rng = np.random.default_rng(20261030)
    sample_idx = rng.choice(np.flatnonzero(fp.ravel()), size=300000, replace=False)
    cand_s = out_arr.ravel()[sample_idx].astype(np.float64)
    for f in sorted((rc.DATA / "registry_focus").glob("*.tif")):
        with rasterio.open(f) as s:
            ref = s.read(1).astype(np.float32)
        ref_dots = np.isfinite(ref) & (ref > 0) & fp
        frac_cand_near_ref = dots_within(dots, ref_dots)
        frac_ref_near_cand = dots_within(ref_dots, dots)
        rho = float(spearmanr(cand_s, np.nan_to_num(ref.ravel()[sample_idx]).astype(np.float64)).statistic)
        uniq[f.stem] = {"candidate_dots_within_3px_of_reference": round(frac_cand_near_ref, 5),
                        "reference_dots_within_3px_of_candidate": round(frac_ref_near_cand, 5),
                        "spearman_rho_300k_footprint_sample": round(rho, 5),
                        "reference_dots": int(ref_dots.sum())}
        print(f.stem, uniq[f.stem], flush=True)
    max_overlap = max(v["candidate_dots_within_3px_of_reference"] for v in uniq.values())
    max_rho = max(abs(v["spearman_rho_300k_footprint_sample"]) for v in uniq.values())
    uniqueness_pass = (max_overlap <= OVERLAP_LIMIT) and (max_rho <= RHO_LIMIT)

    receipt = {
        "file": str(tif.relative_to(ROOT)),
        "sha256": tif_sha,
        "bytes": tif.stat().st_size,
        "submission_name": NAME,
        "note": NOTE,
        "note_chars": len(NOTE),
        "validator": validator,
        "uniqueness": {"per_reference": uniq, "max_candidate_overlap_3px": round(max_overlap, 5),
                       "max_abs_spearman": round(max_rho, 5), "limits": {"overlap": OVERLAP_LIMIT, "rho": RHO_LIMIT},
                       "PASS": uniqueness_pass},
        "score_estimate": {
            "type": "HOLDOUT-DTI proxy (catalogue labels, east half, frozen q chosen on west half)",
            "evaluator": "src/gems32/metric.py (official continuous-p DTI, alpha 0.2 beta 0.8 R 3 px)",
            "note": "NOT an organizer score. Catalogue labels are the training-era USGS/INGENIOUS faults, not the hidden new-fault test set.",
        },
    }
    rc_path = ROOT / "evidence" / "v4_candidate_e2_fixed_q_frozen.json"
    rc_path.write_text(json.dumps(receipt, indent=2))
    (dl / f"{NAME}.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps({"sha256": tif_sha, "validator_PASS": validator["PASS"], "uniqueness_PASS": uniqueness_pass,
                      "max_overlap": max_overlap, "max_abs_rho": max_rho}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
