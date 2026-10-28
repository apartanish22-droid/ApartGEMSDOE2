"""Concurrent research files fail the literal lattice rule on saved bytes."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_recorded_lattice_failures_and_pair_relationship():
    path = ROOT / 'evidence/concurrent_three_saved_byte_recheck_20261028.json'
    assert path.read_bytes() == (ROOT / 'docs/data/concurrent_three_saved_byte_recheck_20261028.json').read_bytes()
    audit = json.loads(path.read_text())
    expected = {'H-DIL-GRAV': (36975, 36692),
                'H-MAG-EDGE-SLOPE': (5103418, 5098478),
                'H-DEPTH-COND': (5106385, 5099871)}
    for name, (count, near) in expected.items():
        result = audit['candidates'][name]
        lattice = result['single_lattice_comparison']
        assert lattice['candidate_positive_pixels_inside_mirror'] == count
        assert lattice['candidate_dots_within_3px'] == near
        assert lattice['overlap_fraction'] == pytest.approx(near / count)
        assert not lattice['literal_overlap_gate_pass'] and result['verdict'] == 'negative'
        assert not result['saved_byte_validator']['ok_to_submit']
    pair = audit['mag_depth_pair']
    assert pair['mag_dotset_is_subset_of_depth'] and not pair['dotsets_identical']
    assert not pair['byte_identical']
    assert audit['holdout_dti'] is None and audit['verdict'] == 'negative'
    assert 'Three further lattice failures' in (ROOT / 'docs/index.html').read_text()


def test_concurrent_read_only_replay_if_pinned_inputs_exist():
    if not (ROOT / 'data/audit/lattice.tif').is_file():
        pytest.skip('fetch pinned audit data to replay concurrent saved-byte check')
    from recheck_concurrent_three import recheck
    recorded = json.loads((ROOT / 'evidence/concurrent_three_saved_byte_recheck_20261028.json').read_text())
    assert recheck() == recorded
