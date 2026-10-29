"""Regression tests for the 2026-10-28 H-SPMD EXP-2 deliverable and Run Card."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "evidence/spmd_run_card_20261028.json").read_text())
EXPS = json.loads((ROOT / "evidence/spmd_three_experiments_20261028.json").read_text())
ZEROS = ROOT / CARD["raster"]
NAN = ROOT / CARD["raster_nan_companion"]
ZIP = ROOT / CARD["zip"]


def test_spmd_run_card_fail_closed_and_note_valid():
    assert CARD["verdict"] == "negative"
    assert CARD["organizer_confirmed"] is None
    assert CARD["leaderboard_estimate"] is None
    assert 0 < len(CARD["note"]) == CARD["note_length_chars"] <= 140
    assert CARD["experiments_used"] == 3
    assert len(CARD["all_experiments"]) == 3


def test_spmd_gates_and_holdout_evidence():
    g = CARD["gates"]
    assert g["G1_format_and_saved_bytes"] is True
    assert g["G2a_beats_d28_b2_paired_ci95"] is True
    assert g["G2b_beats_repo_sparse_unique_best_00947"] is True
    assert g["G3_leakage_canary_63ch"] is True
    assert g["G4a_sparse_uniqueness_543_rasters"] is True
    assert g["G4b_literal_all_including_13gemsdoe_lattice_and_malformed"] is False

    h = CARD["holdout_dti"]
    assert h["label"] == "HOLDOUT-DTI"
    assert h["evaluator_version"] == "GEMSDOE32-HIDE-RECOVER-v3.0"
    assert h["withheld_positives"] == 22232
    lo, hi = h["ci95"]
    assert lo < h["point"] < hi
    assert h["point"] > h["archived_repo_sparse_unique_best_point"]
    assert h["paired_vs_fold_honest_d28_b2"]["ci95_strictly_positive"] is True
    assert h["paired_vs_fold_honest_d28_b2"]["ci95_paired_cluster_bootstrap"][0] > 0.0

    # Verify EXP-1 supervised control set new repo holdout record > 0.125
    assert EXPS["experiments"][0]["holdout_hide_and_recover"]["pooled_dti"] > 0.125


def test_spmd_uniqueness_and_canary_thresholds():
    ov = CARD["registry_correlation_overlap"]
    assert ov["extended_registry_rasters_total"] == 549
    assert ov["surface_max_abs_spearman"] <= 0.90
    assert ov["sparse_dots_max_within_3px"] <= 0.70
    assert ov["literal_all_max_within_3px_including_13gemsdoe_lattice"] > 0.70

    can = CARD["leakage_canary"]
    assert can["passed"] is True
    assert can["n_features_tested"] == 63
    assert can["max_oriented_auc"] <= 0.90


def test_spmd_saved_geotiff_and_zip_bytes():
    assert ZEROS.is_file() and NAN.is_file() and ZIP.is_file()
    assert hashlib.sha256(ZEROS.read_bytes()).hexdigest() == CARD["raster_sha256"]
    assert hashlib.sha256(NAN.read_bytes()).hexdigest() == CARD["raster_nan_sha256"]
    assert hashlib.sha256(ZIP.read_bytes()).hexdigest() == CARD["zip_sha256"]
    with zipfile.ZipFile(ZIP) as zf:
        assert zf.namelist() == [ZEROS.name]

    with rasterio.open(ZEROS) as ds:
        assert ds.count == 1
        assert str(ds.crs) == "EPSG:32611"
        assert ds.shape == (3730, 3292)
        assert ds.dtypes[0] == "float32"
        assert ds.nodata is None
        arr = ds.read(1)

    assert np.isfinite(arr).all()
    assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
    assert int((arr > 0.5).sum()) == 34500


def test_spmd_site_page_and_published_json_exist():
    spmd_html = (ROOT / "docs/spmd/index.html").read_text()
    assert CARD["raster_sha256"] in spmd_html
    assert CARD["submission_name"] in spmd_html
    assert CARD["note"] in spmd_html
    assert "DO NOT AUTO-SUBMIT" in spmd_html
    pub_card = json.loads((ROOT / "docs/data/spmd_run_card_20261028.json").read_text())
    assert pub_card["raster_sha256"] == CARD["raster_sha256"]
