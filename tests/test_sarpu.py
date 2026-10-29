"""Unit tests for H-SARPU physical operators, LEFM isomorphism, and two-regime emitter."""
from __future__ import annotations

import numpy as np

from gems32 import sarpu


def test_baranov_pseudogravity_finite_and_masked():
    rng = np.random.default_rng(42)
    h, w = 64, 60
    foot = np.ones((h, w), dtype=bool)
    foot[:4, :] = False
    rtp = rng.normal(0.0, 25.0, size=(h, w)).astype(np.float32)
    rtp[:, 28:32] += 120.0
    out = sarpu._baranov_pseudogravity_grad(rtp, foot)
    assert out.shape == (h, w)
    assert out.dtype == np.float32
    assert np.isfinite(out).all()
    assert np.all(out[~foot] == 0.0)
    assert float(out[foot].max()) > 0.0


def test_anisotropic_strike_plume_propagates_faster_along_strike():
    h, w = 64, 64
    foot = np.ones((h, w), dtype=bool)
    src = np.zeros((h, w), dtype=np.float32)
    src[32, 32] = 10.0
    # Strike along x-axis (tx=1, ty=0)
    tx = np.ones((h, w), dtype=np.float32)
    ty = np.zeros((h, w), dtype=np.float32)
    plume = sarpu._anisotropic_strike_plume(src, tx, ty, foot, n_steps=16)
    assert plume.shape == (h, w)
    assert np.isfinite(plume).all()
    # Along-strike (dx=8) must exceed cross-strike (dy=8)
    assert float(plume[32, 40]) > 2.0 * float(plume[40, 32])


def test_williams_and_crider_pollard_exact_tips_and_relay():
    h, w = 80, 80
    foot = np.ones((h, w), dtype=bool)
    vis = np.zeros((h, w), dtype=bool)
    # Two en-echelon horizontal segments separated by a relay step-over
    vis[36, 12:36] = True
    vis[42, 42:66] = True
    lefm = sarpu.compute_lefm_continuation(vis, foot)
    assert lefm.shape == (h, w, 2)
    assert np.isfinite(lefm).all()
    assert float(lefm.min()) >= 0.0 and float(lefm.max()) <= 1.0
    # Williams Mode-I/II lobe must be much stronger ahead of segment tip (36, 40) than lateral to mid-segment (24, 24)
    assert float(lefm[36, 40, 0]) > 3.0 * float(lefm[22, 24, 0])
    # Crider-Pollard relay stress must peak inside the step-over bridge (39, 39)
    assert float(lefm[39, 39, 1]) > 0.5
    assert float(lefm[39, 39, 1]) > 4.0 * float(lefm[10, 10, 1])


def test_isomorphic_lefm_sampling_withholds_entire_component():
    h, w = 80, 80
    foot = np.ones((h, w), dtype=bool)
    train_dom = np.ones((h, w), dtype=bool)
    vis = np.zeros((h, w), dtype=bool)
    # One completely isolated segment far from any other segment
    vis[40, 20:55] = True
    py, px, lp, uy, ux, lu = sarpu.sample_isomorphic_lefm_dataset(
        train_dom, vis, foot, n_groups=5, max_pos=500, max_unlab=1000, seed=7
    )
    # Because there is only 1 connected component, withholding its fold removes ALL visible pixels -> LEFM on positives == 0!
    assert py.size > 0
    assert np.allclose(lp, 0.0), "Self-component leaked into LEFM continuation features!"


def test_two_regime_submodular_emitter_respects_collar_cap_and_spacing():
    rng = np.random.default_rng(9)
    h, w = 100, 100
    act = np.ones((h, w), dtype=bool)
    playa = np.zeros((h, w), dtype=bool)
    d_vis = np.full((h, w), 25.0, dtype=np.float32)
    d_vis[:, :40] = 6.0   # collar
    d_vis[:, :3] = 1.0    # inside visible fault mask (d_vis <= 2)

    u_col = rng.uniform(0.2, 1.0, size=(h, w)).astype(np.float32)
    u_far = rng.uniform(0.2, 1.0, size=(h, w)).astype(np.float32)
    dots, stats = sarpu.emit_two_regime_dots(
        u_col, u_far, act, d_vis, playa, k_dots=200, collar_frac=0.40, d_collar=15.0, min_sep_px=2.85
    )
    assert stats["n_collar"] <= 80
    assert stats["n_total"] == int((dots > 0.5).sum())
    assert int((dots[d_vis <= 2.0] > 0.5).sum()) == 0
    # Verify pairwise separation > 2.85 px across ALL placed dots (including across collar/far boundary)
    ys, xs = np.nonzero(dots > 0.5)
    dy = ys[:, None] - ys[None, :]
    dx = xs[:, None] - xs[None, :]
    dist2 = dy * dy + dx * dx + np.eye(len(ys)) * 1e6
    assert float(np.sqrt(dist2.min())) > 2.85
