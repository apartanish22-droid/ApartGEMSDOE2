"""Regression tests for the IR-TRACE-02 H2 demo correction (2026-10-28).

H2 (PR #20) was generated from seeded pseudo-features without competition
data, yet was published with conditional submit guidance and a dot-count
score projection.  These tests pin the corrected fail-closed state.
"""
import json
from pathlib import Path

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
