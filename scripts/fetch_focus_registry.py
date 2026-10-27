#!/usr/bin/env python3
"""Fetch every submission-like GeoTIFF from the focus GEMSDOE repositories (the duplicate-gate registry).

Why: the PARALLEL-RUN PROTOCOL requires every new raster to be compared with *all* registry
rasters (rank-correlation > 0.90 or > 70 % of dots within 3 px of one registry raster => duplicate,
stop).  Parallel sessions push new candidates to the focus repositories continuously, so the
registry must be re-enumerated at run time rather than hard-coded.

What it does (no DrivenData access, GitHub only):
  1. resolves the current ``main`` commit SHA of each focus repository (pinned in the manifest);
  2. lists every ``.tif``/``.tiff`` blob under ``docs/``, ``inputs/``, ``archive/``, ``evidence/``
     (competition data under ``data/`` is deliberately excluded: those are inputs, not submissions);
  3. downloads each blob (skipping files already present with the same git blob size) into
     ``.cache/registry/<repo>/<path>`` and records sha256 + bytes + repo + ref + path.

Output: ``registry/focus_registry_manifest.json``.  The cache itself is git-ignored (``.cache/``).

Usage:  python scripts/fetch_focus_registry.py [--repos GEMSDOE24,GEMSDOE25,...] [--jobs 6]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = "buffedlizard55-lab"
FOCUS = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]
PREFIXES = ("docs/", "inputs/", "archive/", "evidence/")
MAX_BYTES = 8_000_000          # submission rasters are < 2 MB; anything larger is a data product


def gh_json(path: str):
    out = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def list_repo(repo: str) -> tuple[str, list[dict]]:
    ref = gh_json(f"repos/{OWNER}/{repo}/commits/main")["sha"]
    tree = gh_json(f"repos/{OWNER}/{repo}/git/trees/{ref}?recursive=1")
    files = [t for t in tree["tree"]
             if t["type"] == "blob" and t["path"].lower().endswith((".tif", ".tiff"))
             and t["path"].startswith(PREFIXES) and int(t.get("size", 0)) <= MAX_BYTES]
    return ref, files


def fetch_one(repo: str, ref: str, path: str, size: int, cache: Path) -> dict:
    dest = cache / repo / path
    if not (dest.exists() and dest.stat().st_size == size):
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".partial")
        for attempt in range(3):
            try:
                with tmp.open("wb") as fh:
                    subprocess.run(["gh", "api", f"repos/{OWNER}/{repo}/contents/{path}?ref={ref}",
                                    "-H", "Accept: application/vnd.github.raw"],
                                   stdout=fh, check=True, stderr=subprocess.PIPE)
                tmp.replace(dest)
                break
            except subprocess.CalledProcessError:
                time.sleep(2 * (attempt + 1))
        else:
            tmp.unlink(missing_ok=True)
            return {"repo": repo, "ref": ref, "path": path, "status": "FAILED"}
    return {"repo": repo, "ref": ref, "path": path, "bytes": dest.stat().st_size,
            "sha256": sha256(dest), "local": str(dest.relative_to(ROOT)), "status": "ok"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repos", default=",".join(FOCUS))
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--cache", default=str(ROOT / ".cache" / "registry"))
    ap.add_argument("--out", default=str(ROOT / "registry" / "focus_registry_manifest.json"))
    a = ap.parse_args()
    cache = Path(a.cache)
    jobs, refs = [], {}
    for repo in a.repos.split(","):
        ref, files = list_repo(repo)
        refs[repo] = ref
        print(f"{repo}: {len(files)} rasters at {ref[:12]}", flush=True)
        jobs += [(repo, ref, f["path"], int(f["size"])) for f in files]
    results = []
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        futs = [ex.submit(fetch_one, *j, cache) for j in jobs]
        for i, f in enumerate(cf.as_completed(futs), 1):
            results.append(f.result())
            if i % 25 == 0:
                print(f"  fetched {i}/{len(jobs)}", flush=True)
    results.sort(key=lambda r: (r["repo"], r["path"]))
    failed = [r for r in results if r["status"] != "ok"]
    manifest = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "owner": OWNER, "refs": refs, "prefixes": list(PREFIXES), "max_bytes": MAX_BYTES,
        "n_rasters": len(results) - len(failed), "n_failed": len(failed), "rasters": results,
        "note": "Registry for the duplicate gate. Hashes are of the fetched bytes at the pinned refs.",
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"wrote {a.out}: {manifest['n_rasters']} rasters, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
