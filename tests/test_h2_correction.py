"""Regression tests for the withdrawn H2 pseudo-feature demo.

H2 was published with unsupported score/uniqueness and download claims. The
artifact is synthetic; no scientific or portal authorization follows from its
format diagnostics. These tests keep the public guidance and legacy CLI closed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import rasterio

ROOT = Path(__file__).resolve().parents[1]
CARD_PATH = ROOT / "docs/data/run_card_h2.json"
SUMMARY_PATH = ROOT / "docs/EXECUTIVE_SUMMARY_H2.md"
STATUS_PATH = ROOT / "assets/SUBMISSION_STATUS.txt"
ARTIFACT = ROOT / "assets/gems-h2-fractal-faultzone-20261028T054632Z-8c5870c5.tif"


def test_h2_run_card_is_withdrawn_and_has_no_scientific_score():
    card = json.loads(CARD_PATH.read_text())
    assert card["record_status"] == "withdrawn_synthetic_demo"
    assert card["verdict"] == "negative"
    assert card["submission_authorized"] is False
    assert card["holdout_dti"] is None
    assert card["evaluator_version"] is None
    assert card["withheld_positive_instances"] is None
    assert card["ci95"] == [None, None]
    assert card["score_label"].startswith("No HOLDOUT-DTI")
    assert card["leakage_canary"]["status"] == "not_run"
    assert card["registry_uniqueness"]["complete_registry_checked"] is False
    assert card["submission_name"] is None
    assert card["submission_note"] is None


def test_h2_user_facing_surfaces_do_not_offer_a_download_or_projection():
    summary = SUMMARY_PATH.read_text()
    status = STATUS_PATH.read_text()

    assert "DO NOT DOWNLOAD OR SUBMIT THIS ARTIFACT" in summary
    assert "seeded pseudo-features" in summary
    assert "New-file leaderboard estimate: not estimable" in summary
    assert "curl -O" not in summary
    assert "Download OK?" not in summary
    assert "0.15–0.35" not in summary
    assert "0.15-0.35" not in summary
    assert "✅ Yes" not in summary
    assert "unique vs" not in summary.lower()
    assert "Complete-registry uniqueness: not established" in summary

    assert "DO NOT SUBMIT any file" in status
    assert "DO NOT DOWNLOAD OR SUBMIT" in status
    assert "OK TO SUBMIT: YES" not in status
    assert "CONDITIONAL YES" not in status


def test_h2_artifact_hash_and_recorded_readback_match():
    card = json.loads(CARD_PATH.read_text())
    digest = hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
    assert digest == card["artifact"]["sha256"]
    with rasterio.open(ARTIFACT) as src:
        assert src.driver == "GTiff"
        assert src.count == 1
        assert src.dtypes[0] == "float32"
        assert [src.height, src.width] == card["validator_output"]["shape"]
        assert str(src.crs) == card["validator_output"]["crs"]
        assert list(src.transform)[:6] == card["validator_output"]["transform"]
        values = src.read(1)
    assert values.size == card["validator_output"]["whole_array_pixel_count"]
    assert int((values > 0).sum()) == card["artifact"]["nonzero_pixels"]
    assert values.min() >= 0.0 and values.max() <= 1.0


def test_h2_legacy_cli_exits_without_writing_a_new_artifact():
    downloads = ROOT / "docs/downloads"
    before = {p.name for p in downloads.glob("gems-h2-fractal-faultzone-*")}
    result = subprocess.run(
        [sys.executable, str(ROOT / "src/generate_h2_fractal_submission.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    after = {p.name for p in downloads.glob("gems-h2-fractal-faultzone-*")}
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr
    assert "withdrawn and disabled" in result.stderr
    assert after == before
