"""Regression tests for the integrated negative decision and saved-byte audit."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from recheck_udsr import verify


def test_udsr_pages_do_not_offer_upload():
    for name in ('index.html', 'executive-summary.html'):
        page = (ROOT / 'docs/udsr' / name).read_text()
        assert 'DO NOT SUBMIT' in page
        assert 'research only' in page.lower()
        for prohibited in ('READY TO DOWNLOAD AND SUBMIT', '100% unique', 'portal-safe', 'ORGANIZER-CONFIRMED', 'Download Validated .TIF'):
            assert prohibited not in page
    card = json.loads((ROOT/'evidence/apartgemsdoe2_run_card_20261027.json').read_text())
    assert card['verdict'] == 'negative'
    assert card['registry_correlation_overlap']['passed'] is False
    assert 'DO NOT SUBMIT' in card['submission_guidance']


def test_site_builds_do_not_restore_unsafe_claims():
    pages = [ROOT/'docs/index.html', *sorted((ROOT/'docs/ap2').glob('*.html'))]
    before = {p: p.read_bytes() for p in pages}
    subprocess.run([sys.executable, 'scripts/build_site.py'], cwd=ROOT, check=True)
    subprocess.run([sys.executable, 'scripts/build_ap2_site.py'], cwd=ROOT, check=True)
    assert before == {p: p.read_bytes() for p in pages}
    homepage = (ROOT/'docs/index.html').read_text()
    assert 'id="leader-value">—</div>' in homepage  # no unverified value if JS is disabled
    assert 'prior run, not independently replayed in this review' in homepage
    assert 'DO NOT SUBMIT without explicit exploratory slot selection' not in homepage
    assert 'error cannot occur here' not in (ROOT/'docs/ap2/how-to-submit.html').read_text()
    assert 'PROJECTION (not a score' not in (ROOT/'docs/ap2/index.html').read_text()


def test_recheck_is_fail_closed_if_data_missing(tmp_path):
    card = json.loads((ROOT/'evidence/apartgemsdoe2_run_card_20261027.json').read_text())
    manifest = json.loads((ROOT/'evidence/history_manifest.json').read_text())
    with pytest.raises(ValueError, match='Missing or hash mismatch'):
        verify(tmp_path/'missing', tmp_path/'lattice', tmp_path/'sample', card, manifest)


def test_recheck_record_and_replay_if_inputs_available():
    record = json.loads((ROOT/'evidence/udsr_independent_recheck_20261028.json').read_text())
    assert record['verdict'] == 'negative'
    assert not record['literal_overlap_gate_pass']
    assert record['candidate_dots_within_3px'] == 26135
    assert record['candidate_positive_pixels_inside_mirror'] == 26173
    assert record['portal_acceptance'] is None
    assert not record['outside_null_or_masked']
    if not (ROOT/'data/audit/lattice.tif').is_file():
        pytest.skip('fetch pinned audit inputs for saved-byte replay')
    card = json.loads((ROOT/'evidence/apartgemsdoe2_run_card_20261027.json').read_text())
    manifest = json.loads((ROOT/'evidence/history_manifest.json').read_text())
    replay = verify(ROOT/card['artifact_paths']['geotiff'], ROOT/'data/audit/lattice.tif', ROOT/'data/audit/mirror_sample.tif', card, manifest)
    assert replay == {k: v for k, v in record.items() if k != 'checked_utc'}
