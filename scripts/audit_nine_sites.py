#!/usr/bin/env python3
"""Audit the nine focus sites (GEMSDOE24/25/27/28/30/31/32/33/36) on identical gates.

Adds to the shared gate runner (scripts/gate_candidates.py):
  * pairwise directional within-3-px overlap and phi (binary Spearman) across the nine best files,
  * a SHA-256 / dot-digest comparison of GEMSDOE25 vs GEMSDOE30 (identical dot counts and metrics
    were reported; the bytes are compared here, not assumed).
Every number is labelled HOLDOUT-DTI (hide-and-recover or SGMC proxy) or a registry/format check.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems32.paths import data_dir  # noqa: E402
from gems32.registry_audit import _phi_binary  # noqa: E402
import gate_candidates as gc  # noqa: E402

SITES = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]
REG = ROOT / ".cache" / "gems_data" / "registry_focus"


def pairwise(files: dict[str, Path], foot: np.ndarray) -> dict:
    dots, dil = {}, {}
    yy, xx = np.ogrid[-3:4, -3:4]
    disk3 = (yy * yy + xx * xx) <= 9
    for name, p in files.items():
        d, _ = gc.read_candidate(p, foot)
        dots[name] = d
        dil[name] = binary_dilation(d, structure=disk3)
    names = list(files)
    within = {a: {} for a in names}
    phi = {a: {} for a in names}
    for a in names:
        for b in names:
            within[a][b] = float(dil[b][dots[a]].mean())  # share of A's dots within 3 px of B's dots
            phi[a][b] = _phi_binary(dots[a][foot], dots[b][foot]) if a != b else 1.0
    return {"within_3px_row_A_in_col_B": within, "phi_binary": phi,
            "dots": {n: int(dots[n].sum()) for n in names}}


def sha_compare(a: Path, b: Path, foot: np.ndarray) -> dict:
    import hashlib
    da, _ = gc.read_candidate(a, foot)
    db, _ = gc.read_candidate(b, foot)
    return {
        "file_a": str(a.relative_to(ROOT)), "file_b": str(b.relative_to(ROOT)),
        "sha256_a": hashlib.sha256(a.read_bytes()).hexdigest(),
        "sha256_b": hashlib.sha256(b.read_bytes()).hexdigest(),
        "bytes_identical": a.read_bytes() == b.read_bytes(),
        "dots_a": int(da.sum()), "dots_b": int(db.sum()),
        "dot_masks_identical": bool(np.array_equal(da, db)),
        "symmetric_difference_dots": int((da ^ db).sum()),
    }


def main() -> int:
    ddir = data_dir()
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    files = {s: REG / f"{s}_best.tif" for s in SITES}
    missing = [s for s, p in files.items() if not p.exists()]
    if missing:
        raise SystemExit(f"missing site files: {missing}")
    gate = gc.run([(s, files[s]) for s in SITES], ROOT / "evidence" / "gates_nine_sites_20261030.json",
                  ROOT / "registry" / "focus_registry_manifest.json", n_null_seeds=3)
    pw = pairwise(files, foot)
    cmp_ = sha_compare(files["GEMSDOE25"], files["GEMSDOE30"], foot)
    out = {
        "schema": "apartgems-nine-site-audit-v1",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "score_labels": {"HOLDOUT-DTI": "local evaluator, not organizer score",
                         "ORGANIZER-CONFIRMED": "none in this audit"},
        "gate_report": "evidence/gates_nine_sites_20261030.json",
        "pairwise": pw,
        "GEMSDOE25_vs_GEMSDOE30": cmp_,
        "summary": {s: {"dots": gate["candidates"][s]["dots"],
                        "HR_HOLDOUT_DTI": gate["candidates"][s]["G2_proxies"]["HOLDOUT-DTI_hide_recover"]["pooled_dti"],
                        "SGMC_raw_HOLDOUT_DTI_proxy": gate["candidates"][s]["G2_proxies"]["SGMC-CAL_off_catalogue_proxy"]["raw_dti"],
                        "SGMC_raw_ci95": gate["candidates"][s]["G2_proxies"]["SGMC-CAL_off_catalogue_proxy"]["raw_ci95"],
                        "G1_format": gate["candidates"][s]["G1_format"]["all_checks_passed"],
                        "G3_literal": gate["candidates"][s]["G3_registry"]["literal_rule_passed"],
                        "G3_worst_within_3px_excluding_space_filling": gate["candidates"][s]["G3_registry"]["worst_within_3px_excluding_space_filling"],
                        "G3_worst_within_3px_excluding_space_filling_raster": gate["candidates"][s]["G3_registry"]["worst_within_3px_excluding_space_filling_raster"]}
                    for s in SITES},
    }
    (ROOT / "evidence" / "audit_nine_sites_20261030.json").write_text(json.dumps(out, indent=2, default=float) + "\n")
    print(json.dumps({"GEMSDOE25_vs_30": cmp_}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
