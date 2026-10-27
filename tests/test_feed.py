from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from refresh_feed import SITES, parse_top_score, refresh


HTML = '''<html><table><tr><th>Rank</th><th>Participant</th><th>Best <br> public DW-Tversky</th></tr>
<tr><td>#1</td><td><a href="/foo">participant123</a><br>20h · 32 submissions</td><td>0.4544</td></tr>
<tr><td>#2</td><td>other</td><td>0.3916</td></tr></table></html>'''


def test_parse_top_score_only_from_right_table_and_exact_cell():
    assert parse_top_score('<table><tr><th>unrelated</th></tr></table>' + HTML) == '0.4544'
    with pytest.raises(ValueError):
        parse_top_score('<h1>Login</h1>')
    with pytest.raises(ValueError):
        parse_top_score(HTML.replace('0.4544', '1.2'))
    with pytest.raises(ValueError):
        parse_top_score(HTML.replace('<td>0.4544</td>', '<td>0.4544</td><td>0.1</td>'))


def test_failed_fetch_never_makes_old_value_fresh():
    previous = {'leaderboard': {'top_public_value': '0.4000', 'last_success_utc': 'old', 'status': 'ok'}, 'site_heads': {'GEMSDOE24': {'head_sha': 'a'*40, 'last_success_utc': 'old', 'status': 'ok'}}}
    def failure(url, **kwargs):
        raise OSError('blocked')
    x = refresh(previous, 'new', get=failure)
    assert x['leaderboard']['top_public_value'] == '0.4000'
    assert x['leaderboard']['last_success_utc'] == 'old'
    assert x['leaderboard']['last_attempt_utc'] == 'new'
    assert x['leaderboard']['status'] == 'stale'
    assert x['site_heads']['GEMSDOE24']['head_sha'] == 'a'*40
    assert x['site_heads']['GEMSDOE24']['status'] == 'stale'
    assert x['site_heads']['GEMSDOE25']['status'] == 'unavailable'


def test_success_and_source_movement_do_not_approve_a_candidate():
    previous = {'site_heads': {'GEMSDOE24': {'head_sha': 'a'*40}}}
    def fake(url, api_token=False):
        return json.dumps({'sha': 'b'*40}) if api_token else HTML
    x = refresh(previous, '2026-10-27T00:00:00Z', get=fake)
    assert x['leaderboard']['top_public_value'] == '0.4544'
    assert x['leaderboard']['status'] == 'ok'
    assert x['site_heads']['GEMSDOE24']['changed_since_previous_check']
    assert x['site_heads']['GEMSDOE25']['changed_since_previous_check'] is None
    assert len(x['site_heads']) == len(SITES)
    assert 'approval' in x['note']


def test_invalid_git_sha_stays_unavailable():
    def fake(url, api_token=False):
        return '{"sha":"abc"}' if api_token else HTML
    result = refresh({}, 'now', get=fake)
    assert all(site['status'] == 'unavailable' for site in result['site_heads'].values())
