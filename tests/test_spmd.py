"""Unit tests for the H-SPMD SAR-PU & Multi-Depth Crustal-Geochemical module."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import spmd  # noqa: E402


def test_spmd_channel_disjointness_invariants():
    """Verify the 61-channel stack indexing and strict DEM/LiDAR separation."""
    assert len(spmd.SPMD_CHANNELS) == 8
    assert len(set(spmd.NON_LIDAR_COLS_61)) == 55
    assert max(spmd.NON_LIDAR_COLS_61) == 57
    lidar_cols = {50, 51, 52, 58, 59, 60}
    assert lidar_cols.isdisjoint(set(spmd.NON_LIDAR_COLS_61))
    dem_cols = {5, 11, 18, 19, 20, 21, 22, 23, 24, 25, 31, 32, 33, 34, 44, 49}
    assert (lidar_cols | dem_cols).isdisjoint(set(spmd.SUBSURFACE_PURE_COLS_61))
    assert len(spmd.SUBSURFACE_PURE_COLS_61) == 39


def test_block_standardize_aligns_shifted_blocks():
    """Per-survey-block median/MAD z-scoring removes constant block datum shifts."""
    rng = np.random.default_rng(42)
    h, w = 40, 50
    foot = np.ones((h, w), dtype=bool)
    grp = np.ones((h, w), dtype=np.uint8)
    grp[:, 25:] = 2
    sig = rng.normal(0.0, 1.0, size=(h, w)).astype(np.float32)
    shifted = sig.copy()
    shifted[:, :25] += 50.0
    shifted[:, 25:] -= 30.0
    z = spmd._block_standardize(shifted, grp, foot)
    assert z.shape == (h, w)
    assert np.isfinite(z).all()
    assert abs(float(np.median(z[:, :25])) - float(np.median(z[:, 25:]))) < 0.25
    assert float(np.corrcoef(z.ravel(), sig.ravel())[0, 1]) > 0.96


def test_sarpu_propensity_recovers_censored_flat_basin_faults():
    """Synthetic SAR-PU test: spy propensity boosts true faults censored in flat deep basins."""
    rng = np.random.default_rng(20261028)
    h, w = 96, 96
    foot = np.ones((h, w), dtype=bool)
    lid_valid = np.ones((h, w), dtype=bool)
    lid_valid[:, 72:] = False  # 25% LiDAR gap on right edge

    base_mm = rng.normal(0.0, 0.4, size=(h, w, 35)).astype(np.float32)
    udsr_mm = rng.normal(0.0, 0.4, size=(h, w, 18)).astype(np.float32)
    spmd_mm = rng.normal(0.0, 0.4, size=(h, w, 8)).astype(np.float32)

    # Top half = steep exposed range front; bottom half = flat deep basin (censored)
    steep = np.zeros((h, w), dtype=bool)
    steep[:48, :] = True
    base_mm[:, :, 18] = np.where(steep, 18.0, 0.5)   # det_elev_slope
    base_mm[:, :, 14] = np.where(steep, 20.0, 900.0) # depth_to_base_surf
    base_mm[:, :, 24] = np.where(steep, 45.0, 1.5)   # relief5

    # True physical fault strikes vertically across BOTH regimes
    true_fault = np.zeros((h, w), dtype=bool)
    true_fault[:, 20:23] = True
    true_fault[:, 60:63] = True

    # Subsurface channels (col 1 rtp, col 17 iso_grav_anom_hg, spmd col 1) see BOTH regimes
    base_mm[:, :, 1] += np.where(true_fault, 3.2, 0.0)
    base_mm[:, :, 17] += np.where(true_fault, 3.0, 0.0)
    spmd_mm[:, :, 1] += np.where(true_fault, 2.8, 0.0)

    # Observed catalogue sees 92% of steep fault pixels, but ONLY 8% of flat-basin fault pixels!
    u = rng.random((h, w))
    visible = true_fault & np.where(steep, u < 0.92, u < 0.08)

    m_sup = spmd.fit_dual_cover_61(
        foot, visible, lid_valid, base_mm, udsr_mm, spmd_mm,
        sarpu=False, seed=11,
    )
    m_sar = spmd.fit_dual_cover_61(
        foot, visible, lid_valid, base_mm, udsr_mm, spmd_mm,
        sarpu=True, gamma_train=0.45, seed=11,
    )

    sl = (slice(0, h), slice(0, w))
    p_sup, e_sup = spmd.predict_dual_cover_61_bbox(
        sl, foot, lid_valid, base_mm, udsr_mm, spmd_mm, m_sup
    )
    p_sar, e_sar = spmd.predict_dual_cover_61_bbox(
        sl, foot, lid_valid, base_mm, udsr_mm, spmd_mm, m_sar
    )
    deconf_sar = p_sar / np.power(e_sar, 0.40)

    assert p_sup.shape == (h, w) and p_sar.shape == (h, w)
    assert np.allclose(e_sup, 1.0)
    assert float(e_sar[~steep].mean()) < float(e_sar[steep].mean())
    assert 0.07 <= m_sar["purged_unlabeled_fraction"] <= 0.17

    hidden_basin_fault = true_fault & (~steep) & (~visible)
    steep_nonfault = (~true_fault) & steep & (~visible)
    ratio_sup = float(p_sup[hidden_basin_fault].mean() / max(p_sup[steep_nonfault].mean(), 1e-6))
    ratio_sar = float(deconf_sar[hidden_basin_fault].mean() / max(deconf_sar[steep_nonfault].mean(), 1e-6))
    assert ratio_sar > ratio_sup


def test_preregistration_and_canary_artifacts_exist():
    """Verify frozen pre-registration and 63-channel leakage canary pass."""
    prereg = ROOT / "knowledge/preregistration_spmd_20261028.md"
    assert prereg.is_file()
    txt = prereg.read_text()
    for token in ("EXP-1", "EXP-2", "EXP-3", "SAR-PU", "GEMSDOE32-HIDE-RECOVER-v3.0"):
        assert token in txt

    canary_path = ROOT / "evidence/spmd_leakage_canary_63ch.json"
    assert canary_path.is_file()
    canary = json.loads(canary_path.read_text())
    assert canary["passed"] is True
    assert canary["n_features_tested"] == 63
    assert float(canary["max_oriented_auc"]) <= 0.90
