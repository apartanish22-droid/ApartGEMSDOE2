"""Regression tests for negative research artifacts and evidence labels."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_legacy_udsr_pages_are_research_only():
    for name in ("index.html", "executive-summary.html"):
        text = (ROOT / "docs/udsr" / name).read_text().lower()
        assert "do not submit" in text
        assert "99.85%" in text
        assert "research only" in text
        for misleading in ("portal-safe", "ready to download and submit", "exploratory slot ok", "organizer-confirmed lb"):
            assert misleading not in text


def test_evidence_and_generator_fail_closed():
    audit = json.loads((ROOT / "evidence/nine_focus_sites_and_candidate_audit.json").read_text())
    candidate = next(r for r in audit["rows"] if r["site"] == "ApartGEMSDOE2 (Ours)")
    assert candidate["unique_vs_all_sites"] is False
    assert "DO NOT SUBMIT" in candidate["submit_recommendation"]
    assert all("ORGANIZER-CONFIRMED" not in r["repo_lb_score_label"] for r in audit["rows"])
    script = (ROOT / "scripts/emit_and_audit_deliverables.py").read_text()
    assert '"unique_vs_all_sites": True' not in script
    assert "OK TO SUBMIT FOR ORTHOGONAL" not in script
    assert "ORGANIZER-CONFIRMED (repo ledger" not in script
