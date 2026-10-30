#!/usr/bin/env python3
"""Recompute cross-site uniqueness for the nine user-listed GEMSDOE site bests.

Inputs: evidence/historical_audit.json (site-best SHA-256 pins, each verified present in
registry/focus_registry_manifest.json), the cached registry bytes from scripts/fetch_full_registry.py,
and the 13GEMSDOE calibration lattice pin in registry/historical-pins.json.
Keys are repository paths, not hashes, so byte-identical copies filed under other sites are kept
and count as duplicates (overlap 1.0). Only the file's OWN registry entry is excluded.
Scores are USER-REPORTED; no organizer receipt exists. Owner-mirror bytes only.
Output: evidence/nine_site_bests_20261030.json
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / ".cache/registry"
RADIUS = 3.0
SHAPE = (3730, 3292)
FOOTPRINT = 5167373  # labels.tif valid cells (see data/prepared_manifest.json)

# Verbatim user-reported site bests (prompt, 2026-10-30). Not verified by any organizer receipt.
USER_REPORTED = {
    "GEMSDOE32": ("h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros", 0.2778),
    "GEMSDOE36": ("anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros", 0.2750),
    "GEMSDOE28": ("h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan", 0.2710),
    "GEMSDOE31": ("h27-4-solo-d28-20261004-8acb75e1-nan", 0.2708),
    "GEMSDOE33": ("h33d-analog-tip-stepover-r30-20261004-cb490425926e", 0.2632),
    "GEMSDOE25": ("dotted-h19-5-d2-8-20261002-e56ea318af89-nan", 0.2600),
    "GEMSDOE30": ("d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca", 0.2600),
    "GEMSDOE24": ("h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan", 0.2477),
    "GEMSDOE27": ("topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan", 0.2449),
}


def dots_of(path: Path):
    with rasterio.open(path) as ds:
        if (ds.height, ds.width) != SHAPE:
            return None
        a = ds.read(1).astype("float64")
    fin = np.isfinite(a)
    d = fin & (a > 0)
    return np.column_stack(np.nonzero(d)).astype(float), int(np.isnan(a).sum())


def main() -> int:
    hist = json.loads((ROOT / "evidence/historical_audit.json").read_text())
    man = json.loads((ROOT / "registry/focus_registry_manifest.json").read_text())
    lat = json.loads((ROOT / "registry/historical-pins.json").read_text())["lattice"]

    entries = []
    for r in man["rasters"]:
        entries.append({"site": r["repo"], "path": r["path"], "sha": r["sha256"],
                        "local": REG / r["repo"] / r["path"], "lattice": False})
    entries.append({"site": "13GEMSDOE", "path": lat["path"], "sha": lat["sha256"],
                    "local": REG / "13GEMSDOE" / lat["path"], "lattice": True})
    # Duplicate-byte groups inside the focus registry (for the irregularity ledger)
    by_sha = collections.defaultdict(list)
    for e in entries[:-1]:
        by_sha[e["sha"]].append(f"{e['site']}:{e['path']}")
    dup_groups = [v for v in by_sha.values() if len(v) > 1]

    trees = {}
    for e in entries:
        got = dots_of(e["local"])
        if got is None:
            e["ok"] = False
            continue
        pts, n_nan = got
        e["ok"] = True
        e["n"] = len(pts)
        e["nan"] = n_nan
        trees[(e["site"], e["path"])] = (cKDTree(pts) if len(pts) else None, pts, e)

    sites_out = []
    for row in hist["sites"]:
        site = row["site"]
        name, score = USER_REPORTED[site]
        own = [e for e in entries if e["sha"] == row["sha256"] and e["site"] == site]
        if not own:
            sites_out.append({"site": site, "status": "own_entry_not_found"})
            continue
        own = own[0]
        _, cand, _ = trees[(own["site"], own["path"])]
        rows = []
        for e in entries:
            if e is own or not e.get("ok"):
                continue
            tree, _, ref = trees[(e["site"], e["path"])]
            if tree is None:
                continue
            d, _ = tree.query(cand, k=1, distance_upper_bound=RADIUS)
            frac = float(np.mean(np.isfinite(d)))
            null = float(1.0 - np.exp(-(ref["n"] / FOOTPRINT) * np.pi * RADIUS ** 2))
            rows.append({"reference": f"{e['site']}:{e['path']}", "site": e["site"], "lattice": e["lattice"],
                         "ref_dots": ref["n"], "within_3px": frac, "random_null": null,
                         "identical_bytes": e["sha"] == own["sha"]})
        nonlat = [r for r in rows if not r["lattice"]]
        other_site = [r for r in nonlat if r["site"] != site]
        best_other_site = max(other_site, key=lambda r: r["within_3px"])
        best_any_nonlat = max(nonlat, key=lambda r: r["within_3px"])
        lat_row = next(r for r in rows if r["lattice"] and r["reference"].endswith(lat["path"]))
        sites_out.append({
            "site": site,
            "user_reported_file": name,
            "user_reported_score": score,
            "score_evidence": "USER-REPORTED / UNVERIFIED (no organizer receipt)",
            "registry_entry": f"{own['site']}:{own['path']}",
            "sha256": own["sha"],
            "dots": int(len(cand)),
            "nan_cells_in_file": own["nan"],
            "format_variant": "nan-outside" if own["nan"] > 0 else "zeros-outside",
            "max_overlap_other_site_nonlattice": best_other_site["within_3px"],
            "max_overlap_other_site_reference": best_other_site["reference"],
            "max_overlap_other_site_random_null": best_other_site["random_null"],
            "identical_bytes_elsewhere_in_registry": [r["reference"] for r in rows if r["identical_bytes"]],
            "max_overlap_any_nonlattice": best_any_nonlat["within_3px"],
            "max_overlap_calibration_lattice": lat_row["within_3px"],
            "lattice_random_null": lat_row["random_null"],
            "literal_unique_vs_other_sites": best_other_site["within_3px"] <= 0.70,
            "literal_unique_vs_all_nonlattice": best_any_nonlat["within_3px"] <= 0.70,
            "literal_unique_incl_lattice": max(r["within_3px"] for r in rows) <= 0.70,
            "references_compared": len(rows),
        })
    out = {
        "schema": "nine-site-bests-audit-v2",
        "utc": "2026-10-30",
        "scope": "Nine user-listed site bests vs the pinned 471-raster focus registry + 13GEMSDOE lattice. "
                 "Own entry excluded; byte-identical copies elsewhere kept. Owner-mirror bytes; not organizer-authenticated.",
        "rule": "Literal protocol: candidate dots within 3 px of any reference's dots; duplicate if > 0.70.",
        "registry_duplicate_byte_groups": dup_groups,
        "sites": sites_out,
    }
    (ROOT / "evidence/nine_site_bests_20261030.json").write_text(json.dumps(out, indent=2))
    for s in sites_out:
        if "status" in s:
            print(s)
            continue
        print(f"{s['site']} {s['user_reported_score']:.4f} dots={s['dots']} fmt={s['format_variant']} "
              f"otherSite={s['max_overlap_other_site_nonlattice']:.4f} null={s['max_overlap_other_site_random_null']:.3f} "
              f"lattice={s['max_overlap_calibration_lattice']:.4f} identicalElsewhere={len(s['identical_bytes_elsewhere_in_registry'])}")
    print("duplicate-byte groups in focus registry:", len(dup_groups))
    return 0


if __name__ == "__main__":
    sys.exit(main())
