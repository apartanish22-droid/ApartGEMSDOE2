from pathlib import Path
import json
import sys
from urllib.request import Request

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from refresh_feed import LEADERBOARD, SITES, SameHostRedirect, published_previous, refresh, request_text


def test_failure_keeps_github_head_stale_but_disables_leaderboard():
    previous = {
        'leaderboard': {'top_public_value': '0.4000', 'last_success_utc': 'old', 'status': 'ok'},
        'site_heads': {'GEMSDOE24': {'head_sha': 'a'*40, 'last_success_utc': 'old', 'status': 'ok'}},
    }
    requested = []
    def failure(url, **kwargs):
        requested.append(url)
        raise OSError('blocked')
    result = refresh(previous, 'new', get=failure)
    assert len(requested) == len(SITES)
    assert all(url.startswith('https://api.github.com/') for url in requested)
    assert result['leaderboard']['status'] == 'disabled'
    assert result['leaderboard']['top_public_value'] is None
    assert result['leaderboard']['last_success_utc'] is None
    assert result['site_heads']['GEMSDOE24']['head_sha'] == 'a'*40
    assert result['site_heads']['GEMSDOE24']['status'] == 'stale'
    assert result['site_heads']['GEMSDOE25']['status'] == 'unavailable'


def test_success_and_source_movement_never_fetch_or_approve_leaderboard():
    previous = {'site_heads': {'GEMSDOE24': {'head_sha': 'a'*40}}}
    requested = []
    def fake(url, api_token=False):
        requested.append(url)
        assert api_token and url.startswith('https://api.github.com/')
        return json.dumps({'sha': 'b'*40})
    result = refresh(previous, '2026-10-28T00:00:00Z', get=fake)
    assert LEADERBOARD not in requested
    assert len(requested) == len(SITES)
    assert result['leaderboard']['status'] == 'disabled'
    assert result['leaderboard']['top_public_value'] is None
    assert result['site_heads']['GEMSDOE24']['changed_since_previous_check']
    assert result['site_heads']['GEMSDOE25']['changed_since_previous_check'] is None
    assert len(result['site_heads']) == len(SITES)
    assert 'approval' in result['note']


def test_invalid_git_sha_stays_unavailable():
    result = refresh({}, 'now', get=lambda url, api_token=False: '{"sha":"abc"}')
    assert all(site['status'] == 'unavailable' for site in result['site_heads'].values())


def test_only_github_hosts_can_be_requested_and_token_is_never_sent_to_pages():
    for url in (LEADERBOARD, 'https://www.drivendata.org/termsofuse/',
                'http://api.github.com/repos/x/y', 'https://api.github.com.evil.test/',
                'https://user@api.github.com/', 'https://api.github.com:8443/'):
        with pytest.raises(ValueError):
            request_text(url)
    with pytest.raises(ValueError):
        request_text('https://apartanish22-droid.github.io/ApartGEMSDOE2/', api_token=True)


def test_cross_host_redirect_to_drivendata_is_blocked():
    req = Request('https://api.github.com/repos/owner/repo/commits/main')
    with pytest.raises(ValueError, match='redirect'):
        SameHostRedirect().redirect_request(req, None, 302, 'Found', {}, LEADERBOARD)


def test_last_published_snapshot_is_a_best_effort_stale_seed():
    seed = {'schema': 'seed', 'leaderboard': {}, 'site_heads': {}}
    saved = {'schema': 'apartgems-public-feed-v1', 'leaderboard': {'top_public_value': '0.5'}, 'site_heads': {}}
    assert published_previous(seed, None) is seed
    assert published_previous(seed, 'https://example.test/feed', get=lambda url: json.dumps(saved)) == saved
    assert published_previous(seed, 'https://example.test/feed', get=lambda url: '{"schema": "wrong"}') is seed
    def failure(url):
        raise OSError('offline')
    assert published_previous(seed, 'https://example.test/feed', get=failure) is seed
