#!/usr/bin/env python3
"""Download and SHA-256-verify every pinned focus-registry raster (471 files, ~393 MB).

Source of truth: registry/focus_registry_manifest.json (owner mirror, pinned commit SHAs).
Hash pins prove mirror consistency only, NOT organizer authentication.
Bytes go to .cache/registry (gitignored). Resumable: files already matching their pin are skipped.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from github_raw import stream_raw  # noqa: E402


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    manifest = json.loads((ROOT / "registry/focus_registry_manifest.json").read_text())
    out_root = ROOT / ".cache/registry"
    failures = []
    t0 = time.time()
    owner = manifest["owner"]
    for i, rec in enumerate(manifest["rasters"], 1):
        full_repo = f"{owner}/{rec['repo']}"
        dest = out_root / rec["repo"] / rec["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_file() and sha256(dest) == rec["sha256"]:
            continue
        fd, tmp_name = tempfile.mkstemp(prefix=".partial.", dir=dest.parent)
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as out:
                stream_raw(full_repo, rec["ref"], rec["path"], out)
            if sha256(tmp) != rec["sha256"]:
                failures.append((full_repo, rec["path"], "sha256 mismatch"))
                continue
            tmp.replace(dest)
        except Exception as exc:  # record and continue; the audit reports failures
            failures.append((full_repo, rec["path"], repr(exc)))
        finally:
            tmp.unlink(missing_ok=True)
        if i % 50 == 0:
            print(f"{i}/{len(manifest['rasters'])} done in {time.time() - t0:.0f}s", flush=True)
    ok = sum(1 for rec in manifest["rasters"] if (out_root / rec["repo"] / rec["path"]).is_file())
    print(f"verified-present {ok}/{len(manifest['rasters'])}; failures {len(failures)}", flush=True)
    for f in failures[:20]:
        print("FAIL", *f, flush=True)
    (ROOT / ".cache/registry_fetch_status.json").write_text(json.dumps(
        {"present": ok, "total": len(manifest["rasters"]), "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
