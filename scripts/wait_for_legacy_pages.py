#!/usr/bin/env python3
"""On a push, let legacy Pages finish before publishing the refreshed feed.

Some repositories have legacy Pages (main /) enabled while also deploying a
scheduled Actions artifact. A push starts both deployments. Waiting avoids the
legacy artifact replacing a newer timestamped feed immediately after it is built.
No repository data is changed and no branch is pushed by this script.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from github_raw import SameHostRedirect

LEGACY_PATH = "dynamic/pages/pages-build-deployment"


def legacy_runs_finished(payload: dict, sha: str) -> bool:
    """A missing run is not evidence that the legacy deploy has finished."""
    runs = payload.get("workflow_runs")
    if not isinstance(runs, list):
        raise ValueError("Invalid workflow-runs response")
    relevant = [r for r in runs if isinstance(r, dict) and r.get("path") == LEGACY_PATH
                and r.get("head_sha") == sha]
    return bool(relevant) and all(r.get("status") == "completed" for r in relevant)


def request_json(repo: str, route: str, token: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/{route}"
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "ApartGEMS-Pages-ordering/1.0",
    })
    with build_opener(SameHostRedirect()).open(request, timeout=30) as response:
        data = json.load(response)
    if not isinstance(data, dict):
        raise ValueError("Invalid GitHub API response")
    return data


def wait_for_legacy(repo: str, sha: str, token: str, *, timeout: int = 600,
                    interval: int = 10, get=request_json, clock=time.monotonic,
                    pause=time.sleep) -> None:
    if (not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo)
            or any(part in (".", "..") for part in repo.split("/"))):
        raise ValueError("Invalid GITHUB_REPOSITORY")
    if not re.fullmatch(r"[0-9a-f]{40}", sha) or not token:
        raise ValueError("A push commit SHA and Actions token are required")
    if timeout <= 0 or interval <= 0:
        raise ValueError("Positive timeout and interval are required")
    pages = get(repo, "pages", token)
    mode = pages.get("build_type")
    if mode == "workflow":
        print("Pages uses Actions-only publishing; no legacy build to wait for.")
        return
    if mode != "legacy":
        raise ValueError(f"Unknown Pages build type: {mode!r}")
    deadline = clock() + timeout
    route = "actions/runs?" + urlencode({"head_sha": sha, "per_page": 100})
    while True:
        if legacy_runs_finished(get(repo, route, token), sha):
            print("Legacy Pages build/deployment finished; refreshing and publishing the feed next.")
            return
        remaining = deadline - clock()
        if remaining <= 0:
            raise TimeoutError("Legacy Pages deployment did not finish; refusing to race it")
        print("Waiting for this commit's legacy Pages deployment...")
        pause(min(interval, remaining))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--interval-seconds", type=int, default=10)
    args = parser.parse_args()
    wait_for_legacy(os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_SHA", ""),
                    os.environ.get("GITHUB_TOKEN", ""), timeout=args.timeout_seconds,
                    interval=args.interval_seconds)


if __name__ == "__main__":
    main()
