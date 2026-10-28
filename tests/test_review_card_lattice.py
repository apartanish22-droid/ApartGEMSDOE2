"""Published review card must agree with the read-back and geometry receipts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_negative_review_card_tracks_saved_bytes_and_scope():
    card = json.loads((ROOT/'evidence/review_card_lattice_20261028.json').read_text())
    readback = json.loads((ROOT/'evidence/trace_readback_20261028.json').read_text())
    lattice = json.loads((ROOT/'evidence/lattice_bounds_20261028.json').read_text())
    candidate = next(c for c in lattice['candidates'] if c['sha256'] == card['raster_sha256'])
    assert card['raster_sha256'] == readback['sha256']
    assert card['registry']['candidate_dots'] == candidate['dots_in_mirror']
    assert card['registry']['independently_rechecked_lattice_dots_within_3px'] == candidate['dots_within_3px_of_lattice']
    assert card['registry']['independently_rechecked_lattice_fraction'] == candidate['fraction_within_3px']
    assert card['validator_output']['outside_null_or_masked'] is readback['checks']['outside_null_or_masked']
    assert card['validator_output']['unmasked_finite_exterior_cells'] == readback['statistics']['outside_not_null_or_masked']
    assert card['validator_output']['no_nan_or_nonfinite_inside_mirrored_footprint'] == readback['checks']['no_nonfinite_inside']
    assert card['validator_output']['shape'] == [readback['properties']['height'], readback['properties']['width']]
    assert card['validator_output']['transform'] == readback['properties']['transform']
    assert card['submission_authorized'] is False
    assert len(card['submission_note']) <= 140
    assert card['new_experiments_this_review'] == card['weekly_slots_used_this_review'] == 0
    assert card['verdict'] == 'negative'
