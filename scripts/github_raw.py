"""Byte-safe, pinned GitHub Contents API downloads for public audit inputs.

The API may label binary bodies as UTF-8. Stream bytes directly instead of
passing them through a CLI text decoder. Credentials, if supplied in the
standard Actions environment, are sent only to api.github.com and never logged.
"""
from __future__ import annotations

import os
import re
import shutil
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


def validate_target(repo: str, ref: str, path: str) -> None:
    if (not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo)
            or any(part in (".", "..") for part in repo.split("/"))):
        raise ValueError(f"Invalid repository: {repo!r}")
    if not re.fullmatch(r"[0-9a-f]{40}", ref):
        raise ValueError("GitHub source must use a full immutable commit SHA")
    if (not path or path.startswith("/") or "\\" in path or "?" in path or "#" in path
            or any(part in ("", ".", "..") for part in path.split("/"))
            or any(ord(char) < 32 for char in path)):
        raise ValueError(f"Unsafe repository path: {path!r}")


class SameHostRedirect(HTTPRedirectHandler):
    """Never send an optional Actions token to another host or over HTTP."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        if target.scheme != "https" or target.netloc.lower() != "api.github.com":
            raise HTTPError(newurl, code, "Refusing cross-host or insecure redirect", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def stream_raw(repo: str, ref: str, path: str, output, *, opener=None, timeout=300) -> None:
    validate_target(repo, ref, path)
    url = f"https://api.github.com/repos/{repo}/contents/{quote(path, safe='/')}?ref={ref}"
    headers = {"Accept": "application/vnd.github.raw+json", "User-Agent": "ApartGEMS-audit/1.0"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    client = opener if opener is not None else build_opener(SameHostRedirect())
    with client.open(request, timeout=timeout) as response:
        shutil.copyfileobj(response, output, length=1024 * 1024)
