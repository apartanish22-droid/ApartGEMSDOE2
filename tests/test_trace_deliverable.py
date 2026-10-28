"""Regression tests for the 2026-10-28 H-TRACE research-only deliverable.

Pins: the emitted bytes match the run card, the verdict stays negative,
the note fits the portal limit, and the -zeros variant is finite [0,1].
Schema mirrors evidence/trace_run_card_20261028.json exactly.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "evidence" / "trace_run_card_20261028.json").read_text())
ZEROS = ROOT / CARD["raster"]
NAN = ZEROS.with_name(ZEROS.name.replace("-zeros.tif", "-nan.tif"))


def test_verdict_negative_and_note_length() -> None:
    assert CARD["verdict"] == "negative"
    assert CARD["leaderboard_estimate"] is None
    assert CARD["organizer_confirmed"] is None
    assert 0 < len(CARD["note"]) == CARD["note_length_chars"] <= 140
    assert CARD["experiments_used"] == 3


def test_gates_recorded_as_measured() -> None:
    g = CARD["gates"]
    assert g["G1_format"] is True
    assert g["G2_holdout_point_and_paired_ci"] is False
    assert g["G3_canary"] is True
    assert g["G4_sparse_uniqueness"] is False
    assert g["G4_literal_including_space_filling_lattice"] is False
    assert CARD["leakage_canary"]["worst_auc_oriented"] <= 0.90


def test_bytes_match_run_card() -> None:
    assert hashlib.sha256(ZEROS.read_bytes()).hexdigest() == CARD["raster_sha256"]
    assert CARD["validator_output"]["writer_audit_zeros"]["sha256"] == CARD["raster_sha256"]
    assert NAN.is_file()
    z = zipfile.ZipFile(ROOT / CARD["zip"])
    assert z.namelist() == [ZEROS.name]


def test_zeros_variant_finite_unit_interval() -> None:
    dots = CARD["registry_correlation_overlap"]["dots"]["candidate_dots"]
    with rasterio.open(ZEROS) as ds:
        assert ds.count == 1 and str(ds.crs) == "EPSG:32611" and ds.shape == (3730, 3292)
        a = ds.read(1)
    assert np.isfinite(a).all()
    assert float(a.min()) >= 0.0 and float(a.max()) <= 1.0
    assert int((a > 0).sum()) == dots == 22438


def test_holdout_labelled_with_evaluator_and_ci() -> None:
    h = CARD["holdout_dti"]
    assert h["label"] == "HOLDOUT-DTI"
    assert h["evaluator_version"] == "GEMSDOE32-HIDE-RECOVER-v3.0"
    assert h["withheld_positives"] == 22232
    lo, hi = h["ci95"]
    assert lo < h["point"] < hi
    assert h["point"] < h["archived_repo_best_point"]
