"""A second unchanged poll must not erase evidence that the audit is old."""
import json
from pathlib import Path

from refresh_feed import load_archive_refs, refresh


def test_feed_persists_drift_against_archive_not_previous_poll():
    refs = {'GEMSDOE24': 'a'*40}
    def get(url, api_token=False):
        if api_token:
            return json.dumps({'sha': 'b'*40})
        raise OSError('leaderboard blocked')
    first = refresh({}, '2026-10-28T00:00:00Z', get=get, archive_refs=refs)
    second = refresh(first, '2026-10-28T01:00:00Z', get=get, archive_refs=refs)
    row = second['site_heads']['GEMSDOE24']
    assert row['changed_since_previous_check'] is False
    assert row['differs_from_archive'] is True
    assert row['audited_archive_ref'] == 'a'*40
    assert second['site_heads']['GEMSDOE25']['differs_from_archive'] is None
    assert second['leaderboard']['status'] == 'unavailable'


def test_invalid_archive_manifest_is_unknown_not_clean(tmp_path):
    path = Path(tmp_path)/'manifest.json'
    path.write_text('{"sites": [{"id":"GEMSDOE24", "ref":"invalid"}]}')
    assert load_archive_refs(path) == {}
    assert load_archive_refs(path/'missing') == {}
    assert len(load_archive_refs()) == 9
