import pytest

from wait_for_legacy_pages import LEGACY_PATH, legacy_runs_finished, wait_for_legacy

SHA = 'a' * 40


def row(status, sha=SHA):
    return {'path': LEGACY_PATH, 'head_sha': sha, 'status': status}


def test_legacy_completion_requires_a_matching_run_and_no_active_runs():
    assert not legacy_runs_finished({'workflow_runs': []}, SHA)
    assert not legacy_runs_finished({'workflow_runs': [row('completed', 'b'*40)]}, SHA)
    assert not legacy_runs_finished({'workflow_runs': [row('completed'), row('in_progress')]}, SHA)
    assert legacy_runs_finished({'workflow_runs': [row('completed')]}, SHA)
    with pytest.raises(ValueError, match='Invalid workflow'):
        legacy_runs_finished({'workflow_runs': None}, SHA)


def test_push_waits_for_actual_legacy_completion_before_returning():
    now = [0]
    states = iter([{'workflow_runs': []}, {'workflow_runs': [row('in_progress')]},
                   {'workflow_runs': [row('completed')]}])
    requested = []
    def get(repo, route, token):
        requested.append(route)
        return {'build_type': 'legacy'} if route == 'pages' else next(states)
    def pause(seconds):
        now[0] += seconds
    wait_for_legacy('owner/repo', SHA, 'test-token', get=get, clock=lambda: now[0], pause=pause)
    assert now[0] == 20
    assert requested[0] == 'pages' and len(requested) == 4
    assert all('head_sha=' + SHA in route for route in requested[1:])


def test_unknown_mode_or_missing_build_fails_closed_and_actions_mode_skips():
    def actions(repo, route, token):
        assert route == 'pages'
        return {'build_type': 'workflow'}
    wait_for_legacy('owner/repo', SHA, 'test-token', get=actions)
    def unknown(repo, route, token):
        return {'build_type': None}
    with pytest.raises(ValueError, match='Unknown Pages'):
        wait_for_legacy('owner/repo', SHA, 'test-token', get=unknown)
    now = [0]
    def absent(repo, route, token):
        return {'build_type': 'legacy'} if route == 'pages' else {'workflow_runs': []}
    with pytest.raises(TimeoutError, match='refusing to race'):
        wait_for_legacy('owner/repo', SHA, 'test-token', timeout=2, interval=1,
                        get=absent, clock=lambda: now[0], pause=lambda seconds: now.__setitem__(0, now[0]+seconds))
