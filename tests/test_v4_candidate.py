"""Tests for the v4 ridge candidate: metric correctness, saved-byte validation and receipts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems32 import metric  # noqa: E402

TIF = ROOT / "docs" / "downloads" / "apartgems-v4-ridge-tmi-isohg-nms-q5pct-20261030.tif"
RECEIPT = ROOT / "evidence" / "v4_candidate_e2_fixed_q_frozen.json"
CANARY = ROOT / "evidence" / "v4_feature_canary.json"
CARD = ROOT / "evidence" / "v4_run_card.json"


def test_official_worked_example_arithmetic():
    """Rules page example: TP=3.00, FP=1.89, FN=2.00 gives TI = 0.60 (alpha 0.2, beta 0.8)."""
    value = 3.00 / (3.00 + 0.2 * 1.89 + 0.8 * 2.00)
    assert round(value, 2) == 0.60


def test_fast_metric_matches_bruteforce_on_random_grid():
    rng = np.random.default_rng(3)
    truth = rng.random((24, 24)) < 0.04
    pred = np.where(rng.random((24, 24)) < 0.15, rng.random((24, 24)), 0.0)
    if not truth.any():
        truth[5, 5] = True
    fast = metric.components(pred, truth)
    slow = metric.dti_bruteforce(pred, truth)
    assert fast["TP_w"] == pytest.approx(slow["tp"], rel=1e-9, abs=1e-9)
    assert fast["FP_w"] == pytest.approx(slow["fp"], rel=1e-9, abs=1e-9)
    assert fast["FN_w"] == pytest.approx(slow["fn"], rel=1e-9, abs=1e-9)


def test_perfect_prediction_scores_one_and_empty_scores_zero():
    truth = np.zeros((10, 10), bool)
    truth[4, 2:8] = True
    perfect = truth.astype(np.float32)
    assert metric.dti_exact(perfect, truth)["dti"] == pytest.approx(1.0, abs=1e-6)
    assert metric.dti_exact(np.zeros_like(perfect), truth)["dti"] == pytest.approx(0.0, abs=1e-9)


def test_saved_candidate_bytes_pass_validator():
    if not TIF.exists():
        pytest.skip("candidate raster not present")
    rasterio = pytest.importorskip("rasterio")
    with rasterio.open(TIF) as src:
        arr = src.read(1)
        assert src.count == 1 and src.dtypes[0] == "float32"
        assert src.crs.to_string() == "EPSG:32611"
        assert (src.height, src.width) == (3730, 3292)
        assert tuple(src.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    inside = arr[~np.isnan(arr)]
    assert np.isfinite(inside).all()
    assert inside.min() >= 0.0 and inside.max() <= 1.0
    assert int((arr > 0).sum()) > 0


def test_receipt_and_run_card_agree_on_sha_and_note_limit():
    receipt = json.loads(RECEIPT.read_text())
    card = json.loads(CARD.read_text())
    assert receipt["note_chars"] == len(receipt["note"]) <= 140
    assert card["file"]["note_chars"] == len(card["file"]["note"]) <= 140
    assert card["file"]["sha256"] == receipt["sha256"]
    assert card["verdict"] == "negative"
    assert card["submit_to_drivendata"].startswith("NO")


def test_feature_canary_below_leakage_threshold():
    data = json.loads(CANARY.read_text())
    assert data["max_two_sided_auc"] <= data["threshold"] == 0.90
    assert len(data["features"]) == 19
