#!/usr/bin/env python3
"""V5 experiment 2: does the label-free ridge ranking beat random at matched dot budgets?

Pre-registered in knowledge/preregistration_v5_visible_exclusion_20261031.md (addendum).

Steps:
  1. Reproduce the v4 base (scripts/build_v4_candidate.py logic) and check it byte-for-byte against
     docs/downloads/apartgems-v4-ridge-tmi-isohg-nms-q5pct-20261030.tif. Stop if it differs.
  2. For N in the pre-registered budgets, take A_N = top-N ridge pixels by score over the footprint
     and R_N = N random ridge pixels (5 seeds).
  3. Score every candidate with the canonical hide-and-recover evaluator (HOLDOUT-DTI). Paired CI on
     (A_N minus the mean of the random controls) from identical resampling indices.

Labels are catalogue-free for construction. Labels appear only in the evaluator, as withheld truth.
    GEMS_DATA_DIR=.cache/gems_data python scripts/run_v5_budget_rank_experiment.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import ridge_candidate_v4 as rc  # noqa: E402
from gems32 import holdout  # noqa: E402
from gems32.paths import data_dir  # noqa: E402

BASE_TIF = ROOT / "docs/downloads/apartgems-v4-ridge-tmi-isohg-nms-q5pct-20261030.tif"
OUT = ROOT / "evidence/v5_budget_rank_experiment_20261031.json"
BUDGETS = (37654, 44090)
RAND_SEEDS = (11, 22, 33, 44, 55)
N_BOOT = 2000
FROZEN_Q = 0.05


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_v4_base(fp: np.ndarray, score: np.ndarray, ridge: np.ndarray) -> np.ndarray:
    H, W = fp.shape
    west = fp.copy()
    west[:, W // 2:] = False
    return rc.build_prediction(score, ridge, fp, west, FROZEN_Q, dilate=False)


def main() -> int:
    ddir = data_dir()
    ctx = holdout.load_holdout_context(ddir)
    fp = rc.load_footprint()
    hg = rc.load_band(rc.BAND["tmi_hg"], fp)
    iso = rc.load_band(rc.BAND["iso_grav_anom_hg"], fp)
    tmi = rc.load_band(rc.BAND["tmi"], fp)
    ny, nx = rc.normal_direction(tmi)
    del tmi
    score = hg + iso
    ridge = rc.nms_across_normal(score, ny, nx) & fp

    # Step 1: reproduce the frozen base and compare bytes.
    base = build_v4_base(fp, score, ridge)
    repro = rc.finalize_output(base, fp)
    tmp = ROOT / ".cache" / "v5_repro_v4.tif"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    rc.write_tif(tmp, repro)
    repro_sha = sha256(tmp)
    file_sha = sha256(BASE_TIF)
    tmp.unlink()
    if repro_sha != file_sha:
        raise SystemExit(f"v4 base not reproduced: {repro_sha} != {file_sha}. Experiment void.")
    with rasterio.open(BASE_TIF) as ds:
        base_file = np.isfinite(ds.read(1)) & (ds.read(1) > 0) & fp
    base_mask = base_file.copy()

    ridge_idx = np.flatnonzero(ridge.ravel())
    order = ridge_idx[np.argsort(-score.ravel()[ridge_idx], kind="stable")]
    H, W = fp.shape

    def mask_from_flat(idx: np.ndarray) -> np.ndarray:
        m = np.zeros(H * W, bool)
        m[idx] = True
        return m.reshape(H, W) & fp

    rows = {}
    boots = {}
    ref = holdout.evaluate_hide_and_recover(base_mask, ctx, b_visible_px=0.0, n_boot=N_BOOT, name="v4_base")
    rows["v4_base_full"] = {"dots": int(base_mask.sum()), "summary": _s(ref)}
    boots["v4_base_full"] = np.asarray(ref["_boots"])

    for n in BUDGETS:
        a_mask = mask_from_flat(order[:n])
        ra = holdout.evaluate_hide_and_recover(a_mask, ctx, b_visible_px=0.0, n_boot=N_BOOT, name=f"A{n}")
        key_a = f"A_top{n}"
        rows[key_a] = {"dots": int(a_mask.sum()), "summary": _s(ra)}
        boots[key_a] = np.asarray(ra["_boots"])

        ctrl = []
        for seed in RAND_SEEDS:
            rng = np.random.default_rng(seed)
            pick = rng.choice(ridge_idx, size=n, replace=False)
            r_mask = mask_from_flat(pick)
            rr = holdout.evaluate_hide_and_recover(r_mask, ctx, b_visible_px=0.0, n_boot=N_BOOT, name=f"R{n}_{seed}")
            ctrl.append({"seed": seed, "dots": int(r_mask.sum()), "summary": _s(rr)})
            boots[f"R{n}_{seed}"] = np.asarray(rr["_boots"])
        rows[f"R_rand{n}"] = ctrl

    paired = {}
    for n in BUDGETS:
        key_a = f"A_top{n}"
        ctrl_pooled = float(np.mean([c["summary"]["pooled_dti"] for c in rows[f"R_rand{n}"]]))
        ctrl_boot = np.mean([boots[f"R{n}_{s}"] for s in RAND_SEEDS], axis=0)
        d = boots[key_a] - ctrl_boot
        lo, hi = float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
        paired[key_a] = {
            "A_pooled_dti": rows[key_a]["summary"]["pooled_dti"],
            "random_mean_pooled_dti": ctrl_pooled,
            "delta_vs_random_mean": rows[key_a]["summary"]["pooled_dti"] - ctrl_pooled,
            "delta_ci95_paired_bootstrap": [lo, hi],
            "promote_rule_pass": bool(rows[key_a]["summary"]["pooled_dti"] > ctrl_pooled and lo > 0.0),
        }

    passed = [k for k, v in paired.items() if v["promote_rule_pass"]]
    report = {
        "schema": "v5-budget-rank-experiment-v1",
        "experiment": "E2 of 3 (budget-matched ridge ranking vs random ridge pixels)",
        "preregistration": "knowledge/preregistration_v5_visible_exclusion_20261031.md (addendum)",
        "v4_base_reproduced_byte_identical": True,
        "v4_base_sha256": file_sha,
        "ridge_pixels_in_footprint": int(ridge.sum()),
        "labels": {
            "primary": "HOLDOUT-DTI (hide-and-recover, GEMSDOE32-HIDE-RECOVER-v3.0)",
            "organizer_confirmed": None,
        },
        "rows": rows,
        "paired_vs_random": paired,
        "decision": {
            "promoted": passed,
            "verdict": "promote to candidate-check" if passed else "negative: ridge ranking does not beat random at matched budget",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"v4_reproduced": True, "ridge_pixels": int(ridge.sum()), "paired": paired, "decision": report["decision"]}, indent=2))
    return 0


def _s(res: dict) -> dict:
    return {
        "evaluator_version": res["evaluator_version"],
        "score_label": res["score_label"],
        "pooled_dti": res["pooled_dti"],
        "ci95_cluster_bootstrap": res["ci95_cluster_bootstrap"],
        "n_withheld_positives": res["n_withheld_positives"],
        "n_bootstrap_reps": res["n_bootstrap_reps"],
    }


if __name__ == "__main__":
    raise SystemExit(main())
