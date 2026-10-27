#!/usr/bin/env python3
"""Restore SHA-256-verified competition mirrors + focus-9 champions into a data dir.

Mirrors live in sibling GitHub repos (see registry/data_manifest.json, copied from
GEMSDOE32) and are fetched with `gh api ... Accept: application/vnd.github.raw`
(github.com is reachable in restricted sandboxes where dropbox/drivendata are not).
They are owner-supplied mirrors of login-walled DrivenData files: integrity-pinned,
NOT organizer-authenticated.

Usage: python scripts/restore_data.py --target-dir /tmp/gems_data
"""
from __future__ import annotations

import argparse, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(repo: str, ref: str, path: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    with tmp.open("wb") as out:
        subprocess.run(["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}",
                        "-H", "Accept: application/vnd.github.raw"], stdout=out, check=True)
    tmp.replace(dest)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target-dir", default="/tmp/gems_data")
    args = ap.parse_args()
    root = Path(args.target_dir); root.mkdir(parents=True, exist_ok=True)
    man = json.loads((ROOT / "registry/data_manifest.json").read_text())
    want_core = {"training_features", "labels", "sample_submission", "ext_derived_sgmc_faults_100m_u8"}
    for e in man["files"]:
        if e["id"] not in want_core:
            continue
        dest = root / e["dest"]
        if dest.exists() and sha256(dest) == e["sha256"]:
            print(f"present  {e['dest']}"); continue
        if "parts" in e:
            asm = dest.with_suffix(".assembling")
            with asm.open("wb") as out:
                for part in e["parts"]:
                    p = root / "parts" / Path(part).name
                    fetch(e["repo"], e["ref"], part, p)
                    out.write(p.read_bytes()); p.unlink()
            asm.replace(dest)
        else:
            fetch(e["repo"], e["ref"], e["path"], dest)
        got = sha256(dest)
        if got != e["sha256"]:
            raise SystemExit(f"HASH MISMATCH {e['id']}: {got} != {e['sha256']}")
        print(f"restored {e['dest']} sha256={got[:12]}…")
    champs = json.loads((ROOT / "registry/champions.json").read_text())
    focus = json.loads((ROOT / "registry/focus_registry_manifest.json").read_text()) \
        if (ROOT / "registry/focus_registry_manifest.json").exists() else None
    print("champions list:", len(champs["files"]), "(download via GEMSDOE32 focus manifest refs; see evidence/forensic_registry.json)")
    print(f"Data ready in {root}. Next: GEMS_DATA_DIR={root} python scripts/run_experiment.py --variant equal --order raw --tag exp1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
