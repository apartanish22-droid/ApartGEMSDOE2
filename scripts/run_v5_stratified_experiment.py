#!/usr/bin/env python3
"""V5 experiment 3 (final in budget): block-stratified ridge ranking vs uniform random ridge pixels.

Pre-registered in knowledge/preregistration_v5_visible_exclusion_20261031.md (experiment 3 addendum).

The label-free score is hg + iso (as in v4). Within each 16 x 16 evaluator block, keep the top-k_b ridge
pixels, with k_b proportional to that block's share of ridge pixels. Random controls use the same
N and the same seeds as experiment 2.

    GEMS_DATA_DIR=.cache/gems_data python scripts/run_v5_stratified_experiment.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import ridge_candidate_v4 as rc  # noqa: E402
from gems32 import holdout  # noqa: E402
from gems32.paths import data_dir  # noqa: E402
from run_v5_budget_rank_experiment import BUDGETS, RAND_SEEDS, N_BOOT, _s  # noqa: E402

OUT = ROOT / "evidence/v5_stratified_experiment_20261031.json"
GRID_N = 16


def stratified_pick(ridge_idx: np.ndarray, score_flat: np.ndarray, shape: tuple[int, int], n: int) -> np.ndarray:
    ys, xs = np.divmod(ridge_idx, shape[1])
    blk = holdout._spatial_block_index(ys, xs, shape, GRID_N)
    total = ridge_idx.size
    chosen = []
    for b in np.unique(blk):
        members = ridge_idx[blk == b]
        c_b = members.size
        k_b = int(round(n * c_b / total))
        if k_b <= 0:
            continue
        k_b = min(k_b, c_b)
        order = members[np.argsort(-score_flat[members], kind="stable")]
        chosen.append(order[:k_b])
    return np.concatenate(chosen) if chosen else np.empty(0, dtype=np.int64)


def main() -> int:
    ctx = holdout.load_holdout_context(data_dir())
    fp = rc.load_footprint()
    hg = rc.load_band(rc.BAND["tmi_hg"], fp)
    iso = rc.load_band(rc.BAND["iso_grav_anom_hg"], fp)
    tmi = rc.load_band(rc.BAND["tmi"], fp)
    ny, nx = rc.normal_direction(tmi)
    del tmi
    score = hg + iso
    ridge = rc.nms_across_normal(score, ny, nx) & fp
    ridge_idx = np.flatnonzero(ridge.ravel())
    score_flat = score.ravel()
    shape = fp.shape
    H, W = shape

    def mask_from_flat(idx: np.ndarray) -> np.ndarray:
        m = np.zeros(H * W, bool)
        m[idx] = True
        return m.reshape(H, W) & fp

    rows, boots, paired = {}, {}, {}
    for n in BUDGETS:
        s_idx = stratified_pick(ridge_idx, score_flat, shape, n)
        s_mask = mask_from_flat(s_idx)
        rs = holdout.evaluate_hide_and_recover(s_mask, ctx, b_visible_px=0.0, n_boot=N_BOOT, name=f"S{n}")
        key = f"S_strat{n}"
        rows[key] = {"dots": int(s_mask.sum()), "summary": _s(rs)}
        boots[key] = np.asarray(rs["_boots"])

        ctrl = []
        for seed in RAND_SEEDS:
            rng = np.random.default_rng(seed)
            pick = rng.choice(ridge_idx, size=n, replace=False)
            rr = holdout.evaluate_hide_and_recover(mask_from_flat(pick), ctx, b_visible_px=0.0, n_boot=N_BOOT,
                                                   name=f"R{n}_{seed}")
            ctrl.append({"seed": seed, "summary": _s(rr)})
            boots[f"R{n}_{seed}"] = np.asarray(rr["_boots"])
        rows[f"R_rand{n}"] = ctrl

        ctrl_pooled = float(np.mean([c["summary"]["pooled_dti"] for c in ctrl]))
        ctrl_boot = np.mean([boots[f"R{n}_{s}"] for s in RAND_SEEDS], axis=0)
        d = boots[key] - ctrl_boot
        lo, hi = float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
        paired[key] = {
            "S_pooled_dti": rows[key]["summary"]["pooled_dti"],
            "random_mean_pooled_dti": ctrl_pooled,
            "delta_vs_random_mean": rows[key]["summary"]["pooled_dti"] - ctrl_pooled,
            "delta_ci95_paired_bootstrap": [lo, hi],
            "promote_rule_pass": bool(rows[key]["summary"]["pooled_dti"] > ctrl_pooled and lo > 0.0),
        }

    promoted = [k for k, v in paired.items() if v["promote_rule_pass"]]
    report = {
        "schema": "v5-stratified-experiment-v1",
        "experiment": "E3 of 3 (block-stratified ridge ranking vs uniform random ridge pixels)",
        "preregistration": "knowledge/preregistration_v5_visible_exclusion_20261031.md (experiment 3 addendum)",
        "grid_n": GRID_N,
        "ridge_pixels_in_footprint": int(ridge_idx.size),
        "labels": {"primary": "HOLDOUT-DTI (hide-and-recover, GEMSDOE32-HIDE-RECOVER-v3.0)", "organizer_confirmed": None},
        "rows": rows,
        "paired_vs_random": paired,
        "decision": {
            "promoted": promoted,
            "verdict": "promote to candidate-check" if promoted else "negative: block-stratified ranking does not beat random",
        },
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"paired": paired, "decision": report["decision"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
