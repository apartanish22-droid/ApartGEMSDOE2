#!/usr/bin/env python3
"""Run the three pre-declared v4 ridge experiments (see scripts/ridge_candidate_v4.py).

Protocol:
  * tune q on the WEST half of the grid (columns < W/2); evaluate the chosen q on the EAST half;
  * CI: stratified bootstrap over 8 east row-strips (strip components are additive);
  * same-protocol reference: the nine registry focus rasters scored on the same EAST region;
  * every number is a catalogue-proxy DTI (labels = USGS/INGENIOUS catalogue), NOT an
    organizer score and NOT the hidden new-fault test set.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ridge_candidate_v4 as rc  # noqa: E402
from gems32 import metric  # noqa: E402

ROOT = rc.ROOT
REG = rc.DATA / "registry_focus"
QS = [0.002, 0.005, 0.0073, 0.01, 0.015, 0.02, 0.03, 0.05]
N_STRIPS = 8
RNG = np.random.default_rng(20261030)


def strip_bootstrap(pred, truth, east, n_boot=2000):
    H = east.shape[0]
    edges = np.linspace(0, H, N_STRIPS + 1).astype(int)
    comps = []
    for a, b in zip(edges[:-1], edges[1:]):
        reg = np.zeros_like(east)
        reg[a:b] = east[a:b]
        c = metric.components(pred, truth, valid=reg)
        comps.append((c["TP_w"], c["FP_w"], c["FN_w"]))
    comps = np.array(comps)
    base = metric.dti(*comps.sum(0))
    boots = []
    for _ in range(n_boot):
        idx = RNG.integers(0, N_STRIPS, N_STRIPS)
        t, f, n = comps[idx].sum(0)
        boots.append(metric.dti(t, f, n))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(base), float(lo), float(hi)


def main() -> int:
    fp = rc.load_footprint()
    truth = rc.load_labels()
    H, W = fp.shape
    west = fp.copy(); west[:, W // 2:] = False
    east = fp.copy(); east[:, :W // 2] = False

    hg = rc.load_band(rc.BAND["tmi_hg"], fp)
    iso = rc.load_band(rc.BAND["iso_grav_anom_hg"], fp)
    tmi = rc.load_band(rc.BAND["tmi"], fp)
    ny, nx = rc.normal_direction(tmi)
    del tmi

    experiments = {
        "E1_ridge_tmi_hg": dict(score=hg, dilate=False),
        "E2_ridge_tmi_hg+iso_hg": dict(score=hg + iso, dilate=False),
        "E3_E2_plus_1px_ring": dict(score=hg + iso, dilate=True),
    }
    report = {"protocol": "tune q on west half, evaluate on east half; catalogue-proxy DTI",
              "metric": "src/gems32/metric.py (official continuous-p DTI, alpha 0.2, beta 0.8, R=3px)",
              "footprint_cells": int(fp.sum()), "truth_cells_total": int(truth.sum()),
              "truth_cells_west": int((truth & west).sum()), "truth_cells_east": int((truth & east).sum()),
              "experiments": {}}
    for name, cfg in experiments.items():
        ridge = rc.nms_across_normal(cfg["score"], ny, nx) & fp
        tune_rows = []
        for q in QS:
            pred = rc.build_prediction(cfg["score"], ridge, fp, west, q, cfg["dilate"])
            r = rc.score_region(pred, truth, west)
            tune_rows.append({"q": q, "west_DTI": r["DTI"], "dots": int((pred > 0).sum())})
            print(f"{name} q={q:.4f} west DTI={r['DTI']:.5f} dots={(pred > 0).sum()}", flush=True)
        best = max(tune_rows, key=lambda x: x["west_DTI"])
        pred = rc.build_prediction(cfg["score"], ridge, fp, west, best["q"], cfg["dilate"])
        # Evaluate the frozen q on the east half
        pred_east = rc.build_prediction(cfg["score"], ridge, fp, west, best["q"], cfg["dilate"])
        east_r = rc.score_region(pred_east, truth, east)
        dti_e, lo, hi = strip_bootstrap(pred_east, truth, east)
        report["experiments"][name] = {
            "tuning": tune_rows, "frozen_q": best["q"],
            "east_DTI": dti_e, "east_CI95_strip_bootstrap": [lo, hi],
            "east_TP_w": east_r["TP_w"], "east_FP_w": east_r["FP_w"], "east_FN_w": east_r["FN_w"],
            "east_withheld_truth_cells": east_r["n_truth"],
            "east_dots": int((pred_east > 0).sum()),
        }
        print(f"==> {name}: frozen q={best['q']} EAST DTI={dti_e:.5f} CI95=[{lo:.5f},{hi:.5f}]", flush=True)
        np.save(rc.DATA / f"_cand_{name}.npy", pred_east)

    # Same-protocol reference: nine registry focus rasters + lattice, on the EAST region
    ref = {}
    for f in sorted(REG.glob("*.tif")):
        with rasterio.open(f) as s:
            a = s.read(1).astype(np.float32)
        p = np.where(np.isfinite(a), a, 0.0)
        r = rc.score_region(p, truth, east)
        dti_e, lo, hi = strip_bootstrap(p, truth, east, n_boot=500)
        ref[f.stem] = {"east_DTI": dti_e, "CI95": [lo, hi], "dots": int((p > 0).sum())}
        print(f"reference {f.stem}: east DTI={dti_e:.5f} CI95=[{lo:.5f},{hi:.5f}] dots={(p > 0).sum()}", flush=True)
    report["registry_reference_same_east_region"] = ref

    out = ROOT / "evidence" / "v4_ridge_experiments.json"
    out.write_text(json.dumps(report, indent=2))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
