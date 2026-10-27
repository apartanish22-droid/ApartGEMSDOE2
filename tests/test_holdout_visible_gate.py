from __future__ import annotations

from pathlib import Path
import numpy as np
import pytest
import rasterio

from gems32.paths import data_dir
from gems32.holdout import (
    HOLDOUT_EVALUATOR_VERSION,
    HoldoutContext,
    PreparedCell,
    evaluate_visible_gated_holdout,
    load_holdout_context,
)


def _ddir() -> Path:
    d = data_dir()
    if not (d / "sample_submission.tif").exists():
        pytest.skip("local data cache absent")
    return d


def test_visible_gated_holdout_synthetic_no_cache():
    """Runs in CI even without `.cache/gems_data/` to verify visible-only B-gating algebra."""
    active = np.ones((20, 20), dtype=bool)
    d_vis = np.full((20, 20), 10.0, dtype=np.float32)
    d_vis[5, 5] = 1.5  # inside B=2 halo of a visible fault (false positive)
    dist = np.hypot(np.arange(20)[:, None] - 12, np.arange(20)[None, :] - 12)
    k_dg = np.maximum(1.0 - dist / 3.0, 0.0).astype(np.float32)
    cell = PreparedCell(
        key="draw0_fold0",
        fold=0,
        seed=0,
        bbox=(slice(0, 20), slice(0, 20)),
        active_sub=active,
        truth_coords=(np.array([12]), np.array([12])),
        k_dg_sub=k_dg,
        n_truth=1,
        d_visible_sub=d_vis,
    )
    sgmc_mask = np.zeros_like(active)
    sgmc_mask[15, 15] = True
    dist_sgmc = np.hypot(np.arange(20)[:, None] - 15, np.arange(20)[None, :] - 15)
    ctx = HoldoutContext(
        foot=active,
        labels=np.zeros_like(active),
        sgmc_off=sgmc_mask,
        near_visible=np.zeros_like(active),
        quad=np.zeros((20, 20), dtype=np.int8),
        quad_bboxes={f: (slice(0, 20), slice(0, 20)) for f in (0, 1, 2, 3)},
        cells=[cell],
        sgmc_truth_coords=(np.array([15]), np.array([15])),
        sgmc_k_dg=np.maximum(1.0 - dist_sgmc / 3.0, 0.0).astype(np.float32),
        sgmc_n_truth=1,
        sgmc_quad_truth_coords={
            0: (np.array([15]), np.array([15])),
            1: (np.array([], dtype=int), np.array([], dtype=int)),
            2: (np.array([], dtype=int), np.array([], dtype=int)),
            3: (np.array([], dtype=int), np.array([], dtype=int)),
        },
        sgmc_quad_n_truth={0: 1, 1: 0, 2: 0, 3: 0},
    )
    cand = np.zeros((20, 20), dtype=bool)
    cand[5, 5] = True   # visible-fault flank FP
    cand[12, 12] = True # hidden-fault TP
    r0 = evaluate_visible_gated_holdout(cand, ctx, b_gate_px=0.0, n_boot=50, name="b0")
    r2 = evaluate_visible_gated_holdout(cand, ctx, b_gate_px=2.0, n_boot=50, name="b2")
    assert r2["pooled_dti"] > r0["pooled_dti"] == pytest.approx(1.0 / 1.2)
    assert r2["pooled_dti"] == pytest.approx(1.0)


def test_loaded_context_exposes_exact_fold_visible_catalogues():
    """Shared callers must never reconstruct a fold catalogue from full labels."""
    ctx = load_holdout_context(_ddir())
    assert ctx.visible_by_cell is not None
    assert set(ctx.visible_by_cell) == {cell.key for cell in ctx.cells}
    for cell in ctx.cells:
        visible = ctx.visible_by_cell[cell.key]
        assert visible.shape == ctx.foot.shape
        assert np.array_equal(visible, cell.visible_full)
        assert not np.any(visible & ~ctx.labels)
        hidden_rows, hidden_cols = cell.truth_coords
        rs, cs = cell.bbox
        assert not visible[rs, cs][hidden_rows, hidden_cols].any()


def test_visible_gated_holdout_restores_exact_live_b_ladder():
    """Fixes IR-32-INSTR-03: deriving B-gates only from visible faults per split
    restores the exact 4-point live leaderboard ordering (0.1922 < 0.2600 < 0.2708 < 0.2778)
    and confirms rollover at B=3.
    """
    ddir = _ddir()
    p_h195 = ddir / "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif"
    p_d28 = ddir / "scored/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"
    if not (p_h195.exists() and p_d28.exists()):
        pytest.skip("scored baseline TIFFs absent")
    ctx = load_holdout_context(ddir)

    with rasterio.open(p_h195) as ds:
        h195 = np.isfinite(ds.read(1)) & (ds.read(1) > 0)
    with rasterio.open(p_d28) as ds:
        d28 = np.isfinite(ds.read(1)) & (ds.read(1) > 0)

    r_solid = evaluate_visible_gated_holdout(h195, ctx, b_gate_px=0.0, n_boot=200, name="h19-5-solid")
    r_b0 = evaluate_visible_gated_holdout(d28, ctx, b_gate_px=0.0, n_boot=200, name="d2.8-b0")
    r_b1 = evaluate_visible_gated_holdout(d28, ctx, b_gate_px=1.0, n_boot=200, name="solo-b1")
    r_b2 = evaluate_visible_gated_holdout(d28, ctx, b_gate_px=2.0, n_boot=200, name="champion-b2")
    r_b3 = evaluate_visible_gated_holdout(d28, ctx, b_gate_px=3.0, n_boot=200, name="overpruned-b3")

    assert r_b2["evaluator_version"] == HOLDOUT_EVALUATOR_VERSION
    assert r_b2["n_withheld_positives"] == 22232
    assert r_b2["ci95"][0] <= r_b2["pooled_dti"] <= r_b2["ci95"][1]
    assert r_b2["full_map_emitted_pixels"] == 37654

    # Exact live rank order restored: H19-5 (0.1922) < D2.8 (0.2600) < Solo (0.2708) < Champion (0.2778)
    assert r_solid["pooled_dti"] < r_b0["pooled_dti"] < r_b1["pooled_dti"] < r_b2["pooled_dti"]
    # Over-pruning beyond B=2 hurts pooled DTI (explaining why B=2 is the flank optimum)
    assert r_b3["pooled_dti"] < r_b2["pooled_dti"]
