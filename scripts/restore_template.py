#!/usr/bin/env python3
"""Restore the pinned read-only shared-template *source assets*, not a fork.

Only the assets named in registry/shared-template-pins.json are fetched. This is
not a runnable full checkout and does not restore the prepared feature stack.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from audit_historical import ROOT, fetch_pin, sha256_file


def restore() -> list[dict]:
    manifest = json.loads((ROOT / "registry/shared-template-pins.json").read_text())
    cache = ROOT / ".cache"
    target_root = cache / "template-assets"
    rows = []
    for item in manifest["files"]:
        source = fetch_pin(item, cache / "upstream-blobs")
        # Ignore upstream destinations and derive local names only from the pinned
        # source path. Prevent a malformed manifest from escaping the cache.
        rel = Path(item["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"Unsafe template path: {rel}")
        dest = target_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_symlink():
            raise ValueError(f"Refusing symlink at template destination: {dest}")
        if not dest.exists() or sha256_file(dest) != item["sha256"]:
            fd, tmp_name = tempfile.mkstemp(prefix=".restore-", dir=dest.parent)
            os.close(fd)
            tmp = Path(tmp_name)
            try:
                shutil.copyfile(source, tmp)
                if sha256_file(tmp) != item["sha256"]:
                    raise ValueError(f"Restored template asset changed: {item['id']}")
                tmp.chmod(0o444)
                tmp.replace(dest)
            finally:
                tmp.unlink(missing_ok=True)
        rows.append({"id": item["id"], "path": str(dest.relative_to(ROOT)), "sha256": sha256_file(dest), "matches_pin": sha256_file(dest) == item["sha256"]})
    return rows


if __name__ == "__main__":
    result = restore()
    print(json.dumps({"scope": "read-only pinned source assets; not a complete executable template or cached feature stack", "assets": result}, indent=2))
