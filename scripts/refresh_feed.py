#!/usr/bin/env python3
"""Refresh a timestamped public-source snapshot; never submit or infer a score.

A failed fetch preserves the last successful value with an explicit stale state.
This can run on GitHub Actions, whose egress differs from the Arena sandbox.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "docs/data/source_feed.json"
HISTORY = ROOT / "evidence/history_manifest.json"
LEADERBOARD = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
SITES = (24, 25, 27, 28, 30, 31, 32, 33, 36)


class TableParser(HTMLParser):
    """Collect text cells of top-level HTML tables, tolerating nested markup."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
        if tag == "table":
            self.depth += 1
            if self.depth == 1:
                self.table = []
        elif self.depth == 1 and tag == "tr":
            self.row = []
        elif self.depth == 1 and self.row is not None and tag in ("td", "th"):
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None and not self.hidden:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.hidden:
            self.hidden -= 1
        if self.depth == 1 and tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join(" ".join(self.cell).split()))
            self.cell = None
        elif self.depth == 1 and tag == "tr" and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.depth:
            if self.depth == 1:
                self.tables.append(self.table)
                self.table = None
            self.depth -= 1


def parse_top_score(html: str) -> str:
    parser = TableParser()
    parser.feed(html)
    for table in parser.tables:
        header = " ".join(table[0]).lower() if table else ""
        if "rank" not in header or "tversky" not in header:
            continue
        for row in table[1:]:
            if row and re.fullmatch(r"\s*#?\s*1\s*", row[0]):
                values = [c for c in row[1:] if re.fullmatch(r"(?:0(?:\.\d+)?|1(?:\.0+)?)", c)]
                if len(values) != 1:
                    raise ValueError("Rank-one score missing or ambiguous")
                try:
                    score = Decimal(values[0])
                except InvalidOperation as exc:
                    raise ValueError("Invalid score") from exc
                if not score.is_finite() or not Decimal(0) <= score <= Decimal(1):
                    raise ValueError("Score is outside [0, 1]")
                return values[0]
    raise ValueError("Expected public leaderboard table or rank-one row not found")


def request_text(url: str, *, api_token: bool = False) -> str:
    headers = {"User-Agent": "ApartGEMSDOE2-public-source-monitor/1.0", "Accept": "application/vnd.github+json" if api_token else "text/html"}
    token = os.environ.get("GITHUB_TOKEN") if api_token else None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        # Avoid treating redirects to a login page as leaderboard success.
        if not api_token and "/accounts/login" in response.geturl():
            raise ValueError("Redirected to login")
        data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError("Response exceeded size limit")
        return data.decode("utf-8")


def load_archive_refs(path: Path = HISTORY) -> dict:
    """Map sites to pinned archive commits, never treating a HEAD poll as a re-audit."""
    try:
        inputs = json.loads(path.read_text())["inputs"]
        if not isinstance(inputs, list) or not all(isinstance(row, dict) for row in inputs):
            raise ValueError("Invalid manifest inputs")
        rows = [row for row in inputs if row.get("kind") == "historical"]
        refs = {row["id"]: row["ref"] for row in rows}
        if (len(rows) != len(SITES) or set(refs) != {f"GEMSDOE{n}" for n in SITES}
                or any(not isinstance(ref, str) or not re.fullmatch(r"[0-9a-f]{40}", ref)
                       for ref in refs.values())):
            raise ValueError("Invalid archival references")
        return refs
    except (OSError, ValueError, TypeError, KeyError):
        return {}  # unknown is not a clean audit


def refresh(previous: dict, now: str, get=request_text, archive_refs=None) -> dict:
    if archive_refs is None:
        archive_refs = load_archive_refs()
    leader = dict(previous.get("leaderboard", {}))
    leader.update({"source": LEADERBOARD, "last_attempt_utc": now})
    try:
        value = parse_top_score(get(LEADERBOARD))
    except Exception as exc:  # a failure must never become a fresh value
        leader.update({"status": "stale" if leader.get("last_success_utc") else "unavailable", "last_error": f"{type(exc).__name__}: {str(exc)[:200]}"})
    else:
        leader.update({"status": "ok", "top_public_value": value, "last_success_utc": now, "last_error": None,
                       "observation_method": "automated HTTPS page fetch",
                       "evidence_class": "OFFICIAL PUBLIC LEADERBOARD OBSERVATION (not a file-bound submission receipt)"})

    prev_sites = previous.get("site_heads", {})
    sites = {}
    for n in SITES:
        name = f"GEMSDOE{n}"
        item = dict(prev_sites.get(name, {}))
        item["last_attempt_utc"] = now
        reference = archive_refs.get(name)
        if not isinstance(reference, str) or not re.fullmatch(r"[0-9a-f]{40}", reference):
            reference = None
        item["audited_archive_ref"] = reference
        # Recalculate using the known pinned reference even on a fetch failure;
        # freshness is represented separately by status and last_success_utc.
        old_head = item.get("head_sha")
        item["differs_from_archive"] = (old_head != reference) if reference and isinstance(old_head, str) and re.fullmatch(r"[0-9a-f]{40}", old_head) else None
        api = f"https://api.github.com/repos/buffedlizard55-lab/{name}/commits/main"
        try:
            payload = json.loads(get(api, api_token=True))
            sha = payload["sha"]
            if not re.fullmatch(r"[0-9a-f]{40}", sha):
                raise ValueError("Invalid commit SHA")
        except Exception as exc:
            item.update({"status": "stale" if item.get("last_success_utc") else "unavailable", "last_error": f"{type(exc).__name__}: {str(exc)[:200]}"})
        else:
            old_sha = item.get("head_sha")
            item.update({"status": "ok", "head_sha": sha, "changed_since_previous_check": old_sha != sha if old_sha else None,
                         "differs_from_archive": (sha != reference) if reference else None,
                         "last_success_utc": now, "last_error": None})
        sites[name] = item
    return {"schema": "apartgems-public-feed-v1", "updated_utc": now, "note": "Snapshot only; source movement is not a new audit, score estimate, receipt, or upload approval.", "leaderboard": leader, "site_heads": sites}


def published_previous(seed: dict, url: str | None, get=request_text) -> dict:
    """Use the last deployed snapshot when available; never make failure fresh."""
    if not url:
        return seed
    try:
        previous = json.loads(get(url))
        if (not isinstance(previous, dict)
                or previous.get("schema") != "apartgems-public-feed-v1"
                or not isinstance(previous.get("leaderboard"), dict)
                or not isinstance(previous.get("site_heads"), dict)):
            raise ValueError("Invalid previous feed")
        return previous
    except Exception as exc:
        print(f"Last published snapshot unavailable; using committed seed ({type(exc).__name__}).")
        return seed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-url", help="optional last deployed snapshot for stale-value fallback")
    args = parser.parse_args()
    seed = json.loads(FEED.read_text()) if FEED.exists() else {}
    previous = published_previous(seed, args.previous_url)
    now = datetime.now(timezone.utc).isoformat()
    output = refresh(previous, now)
    FEED.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write prevents partially published JSON.
    tmp = FEED.with_suffix(".tmp")
    tmp.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    tmp.replace(FEED)
    print(f"Leaderboard: {output['leaderboard']['status']}; site heads: {sum(s['status'] == 'ok' for s in output['site_heads'].values())}/{len(SITES)}")
    return 0  # stale/unavailable is represented in the published data


if __name__ == "__main__":
    raise SystemExit(main())
