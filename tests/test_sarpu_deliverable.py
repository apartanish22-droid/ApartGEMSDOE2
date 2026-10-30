"""Regression tests for the 2026-10-28 H-SARPU EXP-2 deliverable, run card, and Pages subsite."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
CARD_PATH = ROOT / "evidence" / "sarpu_run_card_20261028.json"
DOCS_CARD_PATH = ROOT / "docs" / "data" / "sarpu_run_card_20261028.json"
CARD = json.loads(CARD_PATH.read_text())
ZEROS = ROOT / CARD["raster"]
NAN = ROOT / CARD["nan_twin_raster"]
ZIP = ROOT / CARD["zip"]


def test_run_card_synced_and_protocol_compliant() -> None:
    assert CARD_PATH.read_bytes() == DOCS_CARD_PATH.read_bytes()
    assert CARD["verdict"] == "negative"
    assert CARD["organizer_confirmed"] is None
    assert CARD["leaderboard_estimate"] is None
    assert 0 < len(CARD["note"]) == CARD["note_length_chars"] <= 140
    assert CARD["experiments_used"] == 3
    assert len(CARD["all_experiments"]) == 3


def test_archived_metrics_are_superseded_by_fail_closed_review() -> None:
    correction_path = ROOT / "evidence" / "sarpu_review_correction_20261030.json"
    correction = json.loads(correction_path.read_text())
    assert correction_path.read_bytes() == (ROOT / "docs/data/sarpu_review_correction_20261030.json").read_bytes()
    assert correction["verdict"] == "negative"
    assert correction["status"] == "research_only_do_not_submit"
    assert correction["archived_diagnostic"]["label"] == "HOLDOUT-DTI"
    assert correction["archived_diagnostic"]["point"] == CARD["holdout_dti"]["point"]
    assert correction["archived_diagnostic"]["ci95"] == CARD["holdout_dti"]["ci95"]
    assert correction["archived_diagnostic"]["evaluator_version"] == "GEMSDOE32-HIDE-RECOVER-v3.0"
    assert correction["archived_diagnostic"]["withheld_positive_occurrences"] == 22232
    assert correction["archived_diagnostic"]["promotion_valid"] is False
    assert correction["split_geometry"]["within_15px_of_visible_faults"] == 15705
    assert correction["split_geometry"]["partially_scored_component_instances"] == 76
    assert correction["split_geometry"]["requested_buffered_whole_segment_contract_established"] is False
    assert correction["registry_correlation_overlap"]["literal_lattice_overlap_fraction"] == CARD["registry_correlation_overlap"]["dots_literal_space_filling_lattice"]["within_3px_literal"]
    assert correction["registry_correlation_overlap"]["literal_gate_pass"] is False
    assert correction["registry_correlation_overlap"]["complete_current_registry_verified"] is False
    assert correction["raster"]["archived_sha256"] == CARD["raster_sha256"]
    assert correction["submission"]["name"] is correction["submission"]["note"] is None
    assert not correction["submission"]["file_approved"]
    assert not correction["submission"]["selector_approved"] and not correction["submission"]["upload_authorized"]
    assert correction["organizer_confirmed_score"] is None
    assert correction["new_file_leaderboard_estimate"] is None

    # The original card is retained as provenance; its old combined-gate flag is explicitly superseded.
    assert CARD["gates"]["calibrated_all_scientific_gates_pass"] is True
    assert "old card's historical gate-pass flags do not supersede" in correction["reason"]


def test_geotiff_and_zip_bytes_match_hashes_and_unit_interval() -> None:
    assert ZEROS.is_file() and NAN.is_file() and ZIP.is_file()
    assert hashlib.sha256(ZEROS.read_bytes()).hexdigest() == CARD["raster_sha256"]
    assert hashlib.sha256(NAN.read_bytes()).hexdigest() == CARD["nan_twin_sha256"]
    assert hashlib.sha256(ZIP.read_bytes()).hexdigest() == CARD["zip_sha256"]

    with zipfile.ZipFile(ZIP) as zf:
        assert zf.namelist() == [ZEROS.name]

    with rasterio.open(ZEROS) as ds:
        assert ds.count == 1
        assert str(ds.crs) == "EPSG:32611"
        assert ds.shape == (3730, 3292)
        arr = ds.read(1)
        assert arr.dtype == np.float32
    assert arr.size == 12279160
    assert np.isfinite(arr).all()
    assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
    assert int((arr > 0).sum()) == 37654


def test_sarpu_pages_are_deterministic_and_fail_closed() -> None:
    p_idx = ROOT / "docs" / "sarpu" / "index.html"
    p_gde = ROOT / "docs" / "sarpu" / "executive-summary.html"
    p_fig = ROOT / "docs" / "assets" / "fig6_sarpu_breakthrough.png"
    assert p_idx.is_file() and p_gde.is_file() and p_fig.is_file()

    before = {p: p.read_bytes() for p in (p_idx, p_gde)}
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_site.py")], cwd=ROOT, check=True)
    assert before == {p: p.read_bytes() for p in (p_idx, p_gde)}

    dashboard = p_idx.read_text()
    guide = p_gde.read_text()
    assert CARD["raster_sha256"] in dashboard
    assert CARD["submission_name"] in dashboard  # embedded in archived filename only
    assert "HOLDOUT-DTI" in dashboard
    assert "DO NOT SUBMIT" in dashboard and "negative release verdict" in dashboard
    assert "Download archived TIFF for research — DO NOT SUBMIT" in dashboard
    assert "New-file leaderboard estimate: <strong>not estimable</strong>" in dashboard
    assert "ready for selector review" not in dashboard
    assert "Download Validated" not in dashboard
    assert "Unique Submission Name" not in dashboard

    assert "NO FILE APPROVED — DO NOT SUBMIT" in guide
    assert "There is no approved path, name or note today." in guide
    assert "does not implement authenticated submission automation" in guide
    assert "Predicted values must be in range [0, 1]" in guide
    assert CARD["submission_name"] not in guide
    assert CARD["note"] not in guide
    assert "downloads/" not in guide
