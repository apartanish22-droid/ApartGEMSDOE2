"""Regression tests for the IR-TRACE-02 H2 demo correction (2026-10-28).

H2 (PR #20) was generated from seeded pseudo-features without competition
data, yet was published with conditional submit guidance and a dot-count
score projection.  These tests pin the corrected fail-closed state.
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_h2_run_card_verdict_is_negative():
    card = json.loads((ROOT / "docs/data/run_card_h2.json").read_text())
    assert card["verdict"] == "negative"
    assert card["holdout_dti"] is None
    assert card["correction_20261028"]["ok_to_submit"] is False
    assert card["correction_20261028"]["irregularity_id"] == "IR-TRACE-02"


def test_h2_pages_do_not_offer_conditional_submit():
    summary = (ROOT / "docs/EXECUTIVE_SUMMARY_H2.md").read_text()
    assert "DO NOT SUBMIT THE H2 FILE" in summary
    assert "OK TO SUBMIT: NO" in summary
    status = (ROOT / "assets/SUBMISSION_STATUS.txt").read_text()
    assert "DO NOT SUBMIT THE H2 FILE" in status
    assert "CONDITIONAL YES — pending final validation" not in status
    assert "Portal-safe: YES" not in status
    assert "✅ YES (format validated)" not in summary


def test_h2_saved_byte_audit_is_negative_and_cannot_be_mislabeled():
    audit = json.loads((ROOT / 'evidence/h2_saved_byte_recheck_20261028.json').read_text())
    assert audit['pixel_counts'] == {
        'mirror_footprint_pixels': 5167373,
        'masked_inside_mirror_footprint': 5140874,
        'positive_inside_mirror_footprint': 26499,
        'positive_outside_mirror_footprint': 34897,
        'positive_whole_raster': 61396,
    }
    comp = audit['single_lattice_comparison']
    assert comp['candidate_dots_within_3px'] == 26478
    assert comp['overlap_fraction'] == pytest.approx(26478 / 26499)
    assert not comp['literal_overlap_gate_pass']
    assert not audit['saved_byte_validator']['checks']['no_masked_inside']
    assert audit['saved_byte_validator']['properties']['nodata'] == '0.0'
    assert not audit['saved_byte_validator']['ok_to_submit']
    assert audit['holdout_dti'] is None and audit['verdict'] == 'negative'


def test_h2_read_only_replay_if_pinned_inputs_exist():
    if not (ROOT / 'data/audit/lattice.tif').is_file():
        pytest.skip('fetch pinned audit data to replay saved-byte H2 check')
    from recheck_h2 import recheck
    recorded = json.loads((ROOT / 'evidence/h2_saved_byte_recheck_20261028.json').read_text())
    assert recheck() == recorded
