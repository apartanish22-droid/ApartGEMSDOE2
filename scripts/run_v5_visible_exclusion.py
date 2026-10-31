#!/usr/bin/env python3
"""V5 experiment 1: visible-catalogue exclusion on the label-free v4 ridge base.

Pre-registered in knowledge/preregistration_v5_visible_exclusion_20261031.md.

Uses the repository's canonical hide-and-recover evaluator (gems32.holdout) with its
`b_visible_px` argument, which removes predictions only within B px of VISIBLE faults of each
withheld cell. Withheld labels never enter the candidate. Paired differences use the same
bootstrap resampling indices (same seed, same active blocks), so they are paired.

Outputs evidence/v5_visible_exclusion_20261031.json. Every DTI is labelled HOLDOUT-DTI with its
evaluator version, withheld-positive count and 95% cluster-bootstrap CI. Nothing here is an
organizer score, and nothing here authorises a submission.

    GEMS_DATA_DIR=.cache/gems_data python scripts/run_v5_visible_exclusion.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import holdout  # noqa: E402
from gems32.paths import data_dir  # noqa: E402

BASE_TIF = ROOT / "docs/downloads/apartgems-v4-ridge-tmi-isohg-nms-q5pct-20261030.tif"
OUT = ROOT / "evidence/v5_visible_exclusion_20261031.json"
B_VALUES = (1.0, 2.0, 3.0)
RAND_SEEDS = (11, 22, 33, 44, 55)
N_BOOT = 2000


def _read_mask(path: Path, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(1)
    return np.isfinite(a) & (a > 0) & foot


def _pooled_summary(res: dict) -> dict:
    return {
        "evaluator_version": res["evaluator_version"],
        "score_label": res["score_label"],
        "b_visible_px": res["b_visible_px"],
        "pooled_dti": res["pooled_dti"],
        "ci95_cluster_bootstrap": res["ci95_cluster_bootstrap"],
        "n_withheld_positives": res["n_withheld_positives"],
        "n_spatial_clusters": res["n_spatial_clusters"],
        "n_bootstrap_reps": res["n_bootstrap_reps"],
        "per_quadrant_dti": res["per_quadrant_dti"],
    }


def main() -> int:
    ddir = data_dir()
    ctx = holdout.load_holdout_context(ddir)
    base = _read_mask(BASE_TIF, ctx.foot)
    n_base = int(base.sum())

    # Labelled DTI results for each B, plus the reference C0 (B = 0).
    results: dict[str, dict] = {}
    boots: dict[str, np.ndarray] = {}
    c0 = holdout.evaluate_hide_and_recover(base, ctx, b_visible_px=0.0, n_boot=N_BOOT, name="C0")
    results["C0"] = _pooled_summary(c0)
    boots["C0"] = np.asarray(c0["_boots"])

    retained_at_b2 = None
    emitted_c0 = int(sum(v["emitted"] for v in c0["folds"].values()))
    for b in B_VALUES:
        res = holdout.evaluate_hide_and_recover(base, ctx, b_visible_px=b, n_boot=N_BOOT, name=f"B{int(b)}")
        key = f"B{int(b)}"
        results[key] = _pooled_summary(res)
        boots[key] = np.asarray(res["_boots"])
        if int(b) == 2:
            # Number of dots retained by the B = 2 rule, for the random-thinning control.
            retained_at_b2 = int(sum(v["emitted"] for v in res["folds"].values()))

    # Paired differences against C0 (same resampling indices, so this is a paired bootstrap).
    paired = {}
    for key in ("B1", "B2", "B3"):
        d = boots[key] - boots["C0"]
        lo, hi = float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
        paired[key] = {
            "delta_pooled_dti": results[key]["pooled_dti"] - results["C0"]["pooled_dti"],
            "delta_ci95_paired_bootstrap": [lo, hi],
            "lower_bound_positive": bool(lo > 0.0),
        }

    # Random-thinning control: same retained fraction as the B = 2 rule, no catalogue information.
    # Ratio of emitted dots scored by the evaluator (sum over withheld cells), B = 2 versus C0.
    keep_frac = retained_at_b2 / emitted_c0
    ctrl_rows = []
    ys, xs = np.nonzero(base)
    for seed in RAND_SEEDS:
        rng = np.random.default_rng(seed)
        keep = rng.random(ys.size) < keep_frac
        m = np.zeros_like(base)
        m[ys[keep], xs[keep]] = True
        r = holdout.evaluate_hide_and_recover(m, ctx, b_visible_px=0.0, n_boot=N_BOOT, name=f"rand{seed}")
        ctrl_rows.append({"seed": seed, "dots": int(m.sum()), **_pooled_summary(r)})
    ctrl_mean = float(np.mean([row["pooled_dti"] for row in ctrl_rows]))

    # Off-catalogue SGMC check: the B exclusion here uses the full catalogue, as the final
    # submission would. The SGMC truth is never used to build the candidate.
    labels = ctx.labels
    d_lab = distance_transform_edt(~labels)
    sgmc = {}
    for label, mask in (
        ("C0", base),
        ("B1", base & (d_lab > 1.0)),
        ("B2", base & (d_lab > 2.0)),
        ("B3", base & (d_lab > 3.0)),
    ):
        r = holdout.evaluate_sgmc_with_ci(mask, ctx, n_boot=N_BOOT, name=label)
        sgmc[label] = {
            "evaluator_version": r["evaluator_version"],
            "score_label": r["score_label"],
            "dots": int(mask.sum()),
            "n_withheld_positives": r["n_withheld_positives"],
            "raw_pooled_dti": r["sgmc_raw_pooled_dti"],
            "raw_ci95": r["sgmc_raw_ci95"],
            "prevalence_calibrated_dti": r["sgmc_prevalence_calibrated_dti"],
            "calibrated_ci95": r["sgmc_calibrated_ci95"],
        }

    best_b = max(("B1", "B2", "B3"), key=lambda k: results[k]["pooled_dti"])
    gate_pass = bool(
        paired[best_b]["lower_bound_positive"]
        and results[best_b]["pooled_dti"] > ctrl_mean
    )
    decision = {
        "best_B": best_b,
        "best_B_pooled_dti": results[best_b]["pooled_dti"],
        "best_B_paired_ci95": paired[best_b]["delta_ci95_paired_bootstrap"],
        "random_thinning_mean_at_same_retained_count": ctrl_mean,
        "random_thinning_retained_fraction": keep_frac,
        "promotion_gate_pass": gate_pass,
        "verdict": "promote to candidate-check" if gate_pass else "negative",
    }

    report = {
        "schema": "v5-visible-exclusion-experiment-v1",
        "experiment": "E1 of 3 (visible-catalogue exclusion on label-free v4 base)",
        "preregistration": "knowledge/preregistration_v5_visible_exclusion_20261031.md",
        "base_file": str(BASE_TIF.relative_to(ROOT)),
        "base_dots": n_base,
        "emitted_dots_scored_C0": emitted_c0,
        "emitted_dots_scored_B2": retained_at_b2,
        "labels": {
            "primary": "HOLDOUT-DTI (hide-and-recover, GEMSDOE32-HIDE-RECOVER-v3.0)",
            "secondary": "HOLDOUT-DTI (off-catalogue SGMC, GEMSDOE32-SGMC-CAL-v3.0)",
            "organizer_confirmed": None,
        },
        "hide_and_recover": results,
        "paired_vs_C0": paired,
        "random_thinning_control": {"rows": ctrl_rows, "mean_pooled_dti": ctrl_mean},
        "sgmc_offcatalogue": sgmc,
        "decision": decision,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(decision, indent=2))
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
