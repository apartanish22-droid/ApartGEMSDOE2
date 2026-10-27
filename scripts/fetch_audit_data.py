#!/usr/bin/env python3
"""Fetch immutable GitHub-hosted audit inputs; never download credentials or submit.

The manifest pins owner mirrors and previous submission bytes, not authentic
DrivenData samples or the complete registry. Files are stored outside Git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "evidence/history_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def checked_entries(manifest: dict) -> list[dict]:
    entries = manifest["inputs"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("manifest has no inputs")
    seen = set()
    for entry in entries:
        id_, repo, ref, path, sha = (entry[k] for k in ("id", "repo", "ref", "path", "sha256"))
        if not re.fullmatch(r"[A-Za-z0-9_-]+", id_) or id_ in seen:
            raise ValueError(f"invalid or duplicate id: {id_!r}")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError(f"invalid repo: {repo!r}")
        if not re.fullmatch(r"[0-9a-f]{40}", ref):
            raise ValueError(f"ref must be a full commit SHA: {ref!r}")
        if path.startswith("/") or ".." in Path(path).parts or "?" in path or "#" in path:
            raise ValueError(f"unsafe GitHub path: {path!r}")
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ValueError(f"invalid SHA-256 for {id_}")
        seen.add(id_)
    return entries


def fetch_one(entry: dict, dest: Path) -> str:
    if dest.exists() and sha256_file(dest) == entry["sha256"]:
        return "verified cached bytes"
    dest.parent.mkdir(parents=True, exist_ok=True)
    endpoint = f"repos/{entry['repo']}/contents/{entry['path']}?ref={entry['ref']}"
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as tmp:
            temp_name = tmp.name
            subprocess.run(
                ["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw+json"],
                stdout=tmp, check=True,
            )
        temp = Path(temp_name)
        actual = sha256_file(temp)
        if actual != entry["sha256"]:
            raise ValueError(f"SHA-256 mismatch for {entry['id']}: {actual}")
        temp.replace(dest)
        return "downloaded and verified"
    finally:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=ROOT / "data/audit")
    args = parser.parse_args()
    try:
        entries = checked_entries(json.loads(args.manifest.read_text()))
        for entry in entries:
            result = fetch_one(entry, args.out / f"{entry['id']}.tif")
            print(f"{entry['id']}: {result}")
    except (OSError, KeyError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"FETCH FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
