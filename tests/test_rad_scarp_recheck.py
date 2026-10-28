"""The concurrent RAD-SCARP file fails literal uniqueness and isn't a valid upload."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_recorded_readback_and_legacy_cards_are_fail_closed():
    path = ROOT / 'evidence/rad_scarp_saved_byte_recheck_20261028.json'
    assert path.read_bytes() == (ROOT / 'docs/data/rad_scarp_saved_byte_recheck_20261028.json').read_bytes()
    audit = json.loads(path.read_text())
    comparison = audit['single_lattice_comparison']
    assert comparison['candidate_positive_pixels_inside_mirror'] == 10457
    assert comparison['candidate_dots_within_3px'] == 10421
    assert comparison['overlap_fraction'] == pytest.approx(10421 / 10457)
    assert not comparison['literal_overlap_gate_pass']
    zeros, nan = audit['saved_byte_validator']['zeros'], audit['saved_byte_validator']['nan']
    assert not zeros['checks']['outside_null_or_masked']
    assert zeros['checks']['conservative_strict_whole_array_0_1']
    assert nan['checks']['outside_null_or_masked']
    assert not nan['checks']['conservative_strict_whole_array_0_1']
    assert not zeros['ok_to_submit'] and not nan['ok_to_submit']
    assert audit['holdout_dti'] is None and audit['verdict'] == 'negative'
    old = json.loads((ROOT / 'evidence/rad_scarp_run_card_20261028.json').read_text())
    assert old['unique_vs_gemsdoe_sites'] is None
    assert not old['literal_registry_uniqueness_pass'] and old['holdout_dti'] is None
    assert old['prior_unreproduced_diagnostic']['ci95'] is None
    assert not old['validator_output']['ok_to_submit_on_real_grid']


def test_rad_read_only_replay_if_pinned_inputs_exist():
    if not (ROOT / 'data/audit/lattice.tif').is_file():
        pytest.skip('fetch pinned audit data to replay saved-byte RAD-SCARP check')
    from recheck_rad_scarp import recheck
    recorded = json.loads((ROOT / 'evidence/rad_scarp_saved_byte_recheck_20261028.json').read_text())
    assert recheck() == recorded
