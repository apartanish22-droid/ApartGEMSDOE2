"""Regression tests for the 31 Oct V5 experiment helpers and the uniqueness gate's pure functions."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import run_v5_stratified_experiment as strat  # noqa: E402
import focus_registry_uniqueness as uq  # noqa: E402


def _ridge_fixture(seed=0, shape=(64, 64), density=0.2):
    rng = np.random.default_rng(seed)
    ridge = rng.random(shape) < density
    score = rng.standard_normal(shape)
    idx = np.flatnonzero(ridge.ravel())
    return idx, score.ravel(), shape


def test_stratified_pick_is_subset_of_ridge_and_unique():
    idx, score, shape = _ridge_fixture()
    picked = strat.stratified_pick(idx, score, shape, 300)
    assert picked.size > 0
    assert np.isin(picked, idx).all()
    assert np.unique(picked).size == picked.size


def test_stratified_pick_budget_close_to_target():
    idx, score, shape = _ridge_fixture(seed=3)
    n = 400
    picked = strat.stratified_pick(idx, score, shape, n)
    # Per-block rounding can move the total by at most one dot per occupied block (16 x 16 = 256).
    assert abs(picked.size - n) <= 256


def test_stratified_pick_takes_highest_scores_within_block():
    idx, score, shape = _ridge_fixture(seed=5, density=0.5)
    picked = strat.stratified_pick(idx, score, shape, 50)
    from gems32 import holdout
    ys, xs = np.divmod(idx, shape[1])
    blk = holdout._spatial_block_index(ys, xs, shape, strat.GRID_N)
    for b in np.unique(blk):
        members = idx[blk == b]
        kept = np.intersect1d(members, picked)
        if kept.size == 0 or kept.size == members.size:
            continue
        assert score[kept].min() >= np.sort(score[members])[::-1][kept.size - 1] - 1e-12


def test_footprint_vector_pearson_matches_numpy():
    rng = np.random.default_rng(7)
    field = rng.random((20, 30)).astype(np.float32)
    foot = np.ones_like(field, dtype=bool)
    foot_idx = np.flatnonzero(foot.ravel())
    other = rng.random((20, 30)).astype(np.float32)
    v1 = uq.footprint_vector(field, foot_idx)
    v2 = uq.footprint_vector(other, foot_idx)
    expected = np.corrcoef(field.ravel(), other.ravel())[0, 1]
    assert abs(float(np.dot(v1, v2)) - expected) < 1e-6
