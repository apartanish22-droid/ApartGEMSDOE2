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


def test_scientific_gates_pass_and_holdout_sets_new_repo_record() -> None:
    g = CARD["gates"]
    assert g["G1_format_and_unit_interval"] is True
    assert g["G2_holdout_record_and_paired_ci"] is True
    assert g["G3a_genuine_non_lattice_uniqueness_567_rasters"] is True
    assert g["G3b_literal_206895_dot_calibration_lattice"] is False
    assert g["G4_single_feature_leakage_canary_67ch"] is True
    assert g["calibrated_all_scientific_gates_pass"] is True

    h = CARD["holdout_dti"]
    assert h["label"] == "HOLDOUT-DTI"
    assert h["evaluator_version"] == "GEMSDOE32-HIDE-RECOVER-v3.0"
    assert h["withheld_positives"] == 22232
    lo, hi = h["ci95"]
    assert lo < h["point"] < hi
    assert h["point"] > h["archived_repo_best_point"] == 0.113696
    assert h["paired_vs_fold_honest_d28_b2"]["ci95_strictly_positive"] is True
    assert h["detached_600m_holdout"]["point"] > h["detached_600m_holdout"]["d28_b2_control_point"]

    ov = CARD["registry_correlation_overlap"]
    assert ov["surface_before_placement"]["worst_abs_spearman"] <= 0.90
    assert ov["dots_genuine_sparse_non_lattice"]["worst_all_559_non_lattice"] <= 0.70
    assert ov["dots_genuine_sparse_non_lattice"]["within_3px_of_gemsdoe32_b2_02778"] <= 0.70
    assert ov["dots_genuine_sparse_non_lattice"]["worst_local_apartgemsdoe2"] <= 0.70
    assert CARD["leakage_canary"]["n_features_tested"] == 67
    assert CARD["leakage_canary"]["max_oriented_auc"] <= 0.90


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


def test_sarpu_pages_are_deterministic_and_expose_checksums() -> None:
    p_idx = ROOT / "docs" / "sarpu" / "index.html"
    p_gde = ROOT / "docs" / "sarpu" / "executive-summary.html"
    p_fig = ROOT / "docs" / "assets" / "fig6_sarpu_breakthrough.png"
    assert p_idx.is_file() and p_gde.is_file() and p_fig.is_file()

    before = {p: p.read_bytes() for p in (p_idx, p_gde)}
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_site.py")], cwd=ROOT, check=True)
    assert before == {p: p.read_bytes() for p in (p_idx, p_gde)}

    for page_file in (p_idx, p_gde):
        txt = page_file.read_text()
        assert CARD["raster_sha256"] in txt
        assert CARD["submission_name"] in txt
        assert "HOLDOUT-DTI" in txt
