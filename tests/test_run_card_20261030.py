"""Data-free checks for the 30 Oct 2026 run cards and the submission-folder guard."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "evidence" / "run_card_20261030.json"
REQUIRED = {"lane", "name", "note", "hypothesis", "mechanism", "named_non_fault_mimic",
            "holdout_dti", "registry_correlation_overlap", "raster", "validator_output", "verdict"}


def test_cards_have_required_fields_and_limits():
    doc = json.loads(CARD.read_text())
    assert doc["cards"], "no cards"
    for card in doc["cards"]:
        assert REQUIRED <= set(card), REQUIRED - set(card)
        assert len(card["note"]) <= 140
        assert card["note_chars"] == len(card["note"])
        assert card["verdict"] in {"promote", "negative"}
        # Negative candidates must not be approved for upload anywhere.
        assert card["verdict"] == "negative"
        assert card["holdout_dti"]["organizer_confirmed"] is None
        assert card["validator_output"]["organizer_template_authenticated"] is False
        assert card["raster"]["zeros_outside"]["sha256"] and len(card["raster"]["zeros_outside"]["sha256"]) == 64


def test_no_unapproved_candidate_in_published_downloads():
    # Candidates written this session live under .cache/candidates and must never appear in docs/downloads.
    doc = json.loads(CARD.read_text())
    published = {p.name for p in (ROOT / "docs" / "downloads").glob("*")}
    for card in doc["cards"]:
        stem = Path(card["raster"]["zeros_outside"]["path"]).name
        assert stem not in published
