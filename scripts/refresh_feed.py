#!/usr/bin/env python3
"""Refresh GitHub source HEADs only; never automatically access DrivenData.

DrivenData's terms prohibit automatic website access, including monitoring.
The leaderboard is therefore a link, not a scheduled feed. Last successful
GitHub checks remain dated when an API request fails. No feed entry authorizes
an experiment or a competition submission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
LEADERBOARD = 'https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'
TERMS = 'https://www.drivendata.org/termsofuse/'
SITES = {f'GEMSDOE{n}': f'buffedlizard55-lab/GEMSDOE{n}' for n in (24, 25, 27, 28, 30, 31, 32, 33, 36)}
# The optional seed is our own deployed JSON, not the DrivenData website.
_ALLOWED_HOSTS = {'api.github.com', 'apartanish22-droid.github.io'}


class SameHostRedirect(HTTPRedirectHandler):
    """Do not redirect a scheduled request or GitHub token to another host."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old, new = urlsplit(req.full_url), urlsplit(newurl)
        if (new.scheme != 'https' or new.hostname != old.hostname
                or new.hostname not in _ALLOWED_HOSTS or new.username or new.password
                or new.port not in (None, 443)):
            raise ValueError('Cross-host or unsafe redirects are not allowed')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def request_text(url, *, api_token=False):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in _ALLOWED_HOSTS or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Only the GitHub API and this project\'s Pages host may be fetched')
    if api_token and parsed.hostname != 'api.github.com':
        raise ValueError('GitHub token may only be sent to api.github.com')
    headers = {'User-Agent': 'ApartGEMSDOE2-source-heads/2'}
    if api_token:
        token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
        if token:
            headers['Authorization'] = f'Bearer {token}'
            headers['Accept'] = 'application/vnd.github+json'
    with build_opener(SameHostRedirect()).open(Request(url, headers=headers), timeout=20) as response:
        return response.read().decode('utf-8')


def published_previous(previous, url, get=request_text):
    """Use our published GitHub-only source-head snapshot if available."""
    if not url:
        return previous
    try:
        saved = json.loads(get(url))
        if saved.get('schema') == 'apartgems-public-feed-v1' and isinstance(saved.get('site_heads'), dict):
            return saved
    except Exception:
        pass
    return previous


def refresh(previous, now, get=request_text):
    # Never call `get` for DrivenData, even when previous data says status=ok.
    # Discard any formerly automated value rather than implying it is current.
    leader = {
        'source_url': LEADERBOARD,
        'terms_url': TERMS,
        'top_public_value': None,
        'last_success_utc': None,
        'status': 'disabled',
        'reason': 'Automatic DrivenData website monitoring is disabled under the published terms; consult the official page directly.',
    }
    sites = {}
    for name, repo in SITES.items():
        url = f'https://api.github.com/repos/{repo}/commits/main'
        old = previous.get('site_heads', {}).get(name, {})
        entry = dict(old, repo=repo, source_url=f'https://github.com/{repo}', last_attempt_utc=now)
        try:
            sha = json.loads(get(url, api_token=True))['sha']
            if not re.fullmatch(r'[0-9a-f]{40}', sha):
                raise ValueError('invalid HEAD SHA')
            entry.update(head_sha=sha, last_success_utc=now, status='ok',
                         changed_since_previous_check=(old.get('head_sha') != sha) if old.get('head_sha') else None)
            entry.pop('error', None)
        except Exception as exc:
            entry.update(status='stale' if old.get('head_sha') else 'unavailable',
                         error=f'{type(exc).__name__}: {exc}', changed_since_previous_check=None)
        sites[name] = entry
    return {'schema': 'apartgems-public-feed-v1', 'updated_utc': now,
            'leaderboard': leader, 'site_heads': sites,
            'note': 'GitHub HEAD movement is not a new science audit or submission approval. Automatic leaderboard monitoring is disabled.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'docs/data/source_feed.json')
    parser.add_argument('--previous-url', help='optional published GitHub Pages feed from the prior deployment')
    args = parser.parse_args()
    previous = json.loads(args.out.read_text()) if args.out.exists() else {}
    previous = published_previous(previous, args.previous_url)
    now = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    result = refresh(previous, now)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print('leaderboard monitoring disabled; site HEADs:', sum(x['status'] == 'ok' for x in result['site_heads'].values()), '/', len(SITES))


if __name__ == '__main__':
    main()
