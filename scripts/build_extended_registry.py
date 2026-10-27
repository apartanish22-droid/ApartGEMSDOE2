#!/usr/bin/env python3
"""Build an extended duplicate-gate registry manifest combining:
  1. All 442 live focus-site rasters from GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36.
  2. All historical scored competition rasters from .cache/gems_data/scored/.
  3. Sibling parallel-run GeoTIFFs cloned in /tmp/ref_repos/{GEMSDOE70, KANLERGEMSDOE3, WBGGEMSDOE3} (if present),
     copied into .cache/registry_extra/ so local paths remain relative to ROOT.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path

import rasterio

ROOT = Path(__file__).resolve().parents[1]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    focus_man = json.loads((ROOT / "registry" / "focus_registry_manifest.json").read_text())
    entries = list(focus_man["rasters"])
    seen_sha = {e["sha256"] for e in entries if e.get("status") == "ok"}

    tpl_path = ROOT / ".cache" / "gems_data" / "sample_submission.tif"
    with rasterio.open(tpl_path) as tpl:
        tpl_shape, tpl_crs, tpl_tf = tpl.shape, tpl.crs, tpl.transform

    extra_cache = ROOT / ".cache" / "registry_extra"
    extra_cache.mkdir(parents=True, exist_ok=True)

    # 1. Historical scored rasters
    scored_dir = ROOT / ".cache" / "gems_data" / "scored"
    if scored_dir.is_dir():
        for p in sorted(scored_dir.glob("*.tif")):
            s = sha256(p)
            if s in seen_sha:
                continue
            seen_sha.add(s)
            entries.append(
                {
                    "repo": "HIST_SCORED",
                    "ref": "data_manifest_v1",
                    "path": f"scored/{p.name}",
                    "bytes": p.stat().st_size,
                    "sha256": s,
                    "local": str(p.relative_to(ROOT)),
                    "status": "ok",
                }
            )

    # 2. Sibling parallel repos in /tmp/ref_repos
    ref_root = Path("/tmp/ref_repos")
    for sib in ("GEMSDOE70", "KANLERGEMSDOE3", "WBGGEMSDOE3"):
        sdir = ref_root / sib
        if not sdir.is_dir():
            continue
        for p in sorted(sdir.rglob("*.tif")):
            rel = p.relative_to(sdir).as_posix()
            if rel.startswith(("data/", ".cache/")):
                continue
            if p.stat().st_size > 8_000_000:
                continue
            try:
                with rasterio.open(p) as ds:
                    if ds.count != 1 or ds.shape != tpl_shape or ds.crs != tpl_crs or ds.transform != tpl_tf:
                        continue
            except Exception:
                continue
            s = sha256(p)
            if s in seen_sha:
                continue
            seen_sha.add(s)
            dest = extra_cache / sib / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copy2(p, dest)
            entries.append(
                {
                    "repo": sib,
                    "ref": "head_20261027",
                    "path": rel,
                    "bytes": dest.stat().st_size,
                    "sha256": s,
                    "local": str(dest.relative_to(ROOT)),
                    "status": "ok",
                }
            )

    out_man = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_focus_rasters": focus_man["n_rasters"],
        "n_rasters": len(entries),
        "n_failed": 0,
        "rasters": entries,
        "note": "Extended duplicate-gate registry combining all 9 focus repos + historical scored + sibling parallel repos.",
    }
    out_path = ROOT / "registry" / "extended_registry_manifest.json"
    out_path.write_text(json.dumps(out_man, indent=1) + "\n")
    print(f"Wrote {out_path}: {len(entries)} total rasters ({focus_man['n_rasters']} focus + {len(entries) - focus_man['n_rasters']} extra unique)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
