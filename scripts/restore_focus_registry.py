#!/usr/bin/env python3
"""Restore the pinned focus registry (registry/focus_registry_manifest.json) into .cache/registry.

Fetches exactly the pinned (repo, ref, path) entries through the GitHub Contents API (commit-SHA
pinned, no branch names), verifies every SHA-256 against the manifest, and fails closed on any
mismatch. Nothing is re-enumerated, so the registry cannot drift during a run.

    python scripts/restore_focus_registry.py [--jobs 6]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from github_raw import stream_raw  # noqa: E402

MANIFEST = ROOT / "registry" / "focus_registry_manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_one(entry: dict, owner: str) -> tuple[str, str]:
    dest = ROOT / entry["local"]
    if dest.is_file() and sha256(dest) == entry["sha256"]:
        return entry["local"], "cached"
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + dest.name + ".", suffix=".partial", dir=dest.parent)
    try:
        with open(fd, "wb") as out:
            stream_raw(f"{owner}/{entry['repo']}", entry["ref"], entry["path"], out)
        if sha256(Path(tmp)) != entry["sha256"]:
            raise ValueError(f"hash mismatch: {entry['repo']}:{entry['path']}")
        Path(tmp).replace(dest)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return entry["local"], "fetched"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=6)
    args = ap.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    entries = manifest["rasters"]
    owner = manifest["owner"]
    failures = []
    counts = {"cached": 0, "fetched": 0}
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(fetch_one, e, owner): e for e in entries}
        for fut in cf.as_completed(futs):
            e = futs[fut]
            try:
                _, status = fut.result()
                counts[status] += 1
            except Exception as exc:  # fail closed, but keep going to report all failures
                failures.append(f"{e['repo']}:{e['path']}: {exc}")
    print(json.dumps({"entries": len(entries), **counts, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
