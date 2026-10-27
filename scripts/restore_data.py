#!/usr/bin/env python3
"""Restore integrity-pinned owner mirrors and selected registry references.

This is data ingestion only, not authorization to train, emit, or submit. The
mirror is not organizer-authenticated and the nine focus references plus lattice
are not the complete parallel registry. Large feature shards are streamed.

    python scripts/restore_data.py --target-dir /tmp/gems_data
    python scripts/restore_data.py --target-dir /tmp/gems_data --references-only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from audit_historical import fetch_pin
from github_raw import stream_raw

ROOT = Path(__file__).resolve().parents[1]
CORE_IDS = {"training_features", "labels", "sample_submission", "ext_derived_sgmc_faults_100m_u8"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_destination(root: Path, rel: str) -> Path:
    path = Path(rel)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"Unsafe manifest destination: {rel}")
    dest = root / path
    if dest.is_symlink() or not dest.parent.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Symlink or escaped manifest destination: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or not dest.parent.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Symlink or escaped manifest destination: {dest}")
    return dest


def stream_part(repo: str, ref: str, path: str, out) -> None:
    stream_raw(repo, ref, path, out)


def restore_core_entry(entry: dict, root: Path, stream=stream_part) -> Path:
    dest = safe_destination(root, entry["dest"])
    if dest.is_file() and sha256(dest) == entry["sha256"]:
        return dest
    fd, name = tempfile.mkstemp(prefix="." + dest.name + ".", suffix=".partial", dir=dest.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as out:
            for part in entry.get("parts", [entry.get("path")]):
                if not part:
                    raise ValueError(f"Missing source for {entry['id']}")
                stream(entry["repo"], entry["ref"], part, out)
        actual = sha256(tmp)
        if actual != entry["sha256"]:
            raise ValueError(f"Hash mismatch for {entry['id']}: {actual}")
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)
    return dest


def restore_reference_pins(root: Path, pins: dict, cache: Path, fetch=fetch_pin) -> list[Path]:
    result = []
    named_pins = [(p["site"] + "_best.tif", p) for p in pins["focus"]]
    named_pins.append(("LATTICE_r13.tif", pins["lattice"]))
    for name, pin in named_pins:
        src = fetch(pin, cache)
        if sha256(src) != pin["sha256"]:
            raise ValueError(f"Hash mismatch for reference {name}")
        dest = safe_destination(root, f"registry_focus/{name}")
        if not dest.is_file() or sha256(dest) != pin["sha256"]:
            fd, tmp_name = tempfile.mkstemp(prefix="." + name + ".", suffix=".partial", dir=dest.parent)
            tmp = Path(tmp_name)
            try:
                with os.fdopen(fd, "wb") as out, src.open("rb") as source:
                    shutil.copyfileobj(source, out, length=1 << 20)
                if sha256(tmp) != pin["sha256"]:
                    raise ValueError(f"Copied reference hash mismatch: {name}")
                tmp.replace(dest)
            finally:
                tmp.unlink(missing_ok=True)
        result.append(dest)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target-dir", type=Path, default=Path("/tmp/gems_data"))
    ap.add_argument("--references-only", action="store_true", help="skip the 419 MB feature mirror and other core files")
    args = ap.parse_args()
    root = args.target_dir
    root.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / "registry/data_manifest.json").read_text())
    if not args.references_only:
        entries = [e for e in manifest["files"] if e["id"] in CORE_IDS]
        if {e["id"] for e in entries} != CORE_IDS:
            raise ValueError("The pinned core-data manifest is incomplete")
        for entry in entries:
            dest = restore_core_entry(entry, root)
            print(f"verified {dest.relative_to(root)} sha256={entry['sha256'][:12]}…")
    pins = json.loads((ROOT / "registry/historical-pins.json").read_text())
    refs = restore_reference_pins(root, pins, ROOT / ".cache/audit")
    print(f"Verified {len(refs)} selected references in {root / 'registry_focus'}.")
    print("These owner mirrors are not organizer-authenticated and are not the complete registry. "
          "No experiment or submission is authorized; see evidence/preflight.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
