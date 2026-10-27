#!/usr/bin/env python3
"""Read-only audit of the parallel AP-1 research TIFFs against pinned mirrors.

No model, holdout, training, candidate creation, selector or upload is performed.
The organizer sample is not authenticated here and the full registry is incomplete.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from audit_historical import (
    ROOT, PINS, binary_spearman, directional_overlap, disk, fetch_pin,
    format_checks, load_grid, sha256_file,
)

BASENAME = "apartgemsdoe2-ap1-dilatcond-37654-20261027-1f26aa05"
EXPECTED = {
    "zeros": "973e1615098e5636e9348a3ae1e12d9de392fda2b14f0313c81554cc26274d28",
    "nan": "c12f17f3e7dac14212d3646d7a95fc2a59c962c03363e4836fb3427c291e3682",
}


def audit(cache: Path) -> dict:
    pins = json.loads(PINS.read_text())
    sample, _, sample_grid = load_grid(fetch_pin(pins["sample"], cache))
    foot = np.isfinite(sample)
    if not foot.any():
        raise ValueError("Sample mirror has no footprint")

    variants = {}
    support = None
    for mode in ("zeros", "nan"):
        file = ROOT / "docs/downloads" / f"{BASENAME}-{mode}.tif"
        digest = sha256_file(file)
        if digest != EXPECTED[mode]:
            raise ValueError(f"Saved {mode} TIFF hash differs from the parallel receipt: {digest}")
        arr, mask, grid = load_grid(file)
        if any(grid[k] != sample_grid[k] for k in ("shape", "crs", "transform")):
            raise ValueError(f"Saved {mode} TIFF and provisional sample grid differ")
        if not np.all(np.isfinite(arr[foot]) & ((arr[foot] == 0) | (arr[foot] == 1))):
            raise ValueError(f"Saved {mode} TIFF is not a binary, finite footprint raster")
        dots = foot & (arr > 0)
        if support is None:
            support = dots
        elif not np.array_equal(support, dots):
            raise ValueError("Parallel TIFF twins have different dot support")
        variants[mode] = {
            "file": str(file.relative_to(ROOT)),
            "sha256": digest,
            "positive_pixels_in_footprint": int(dots.sum()),
            "format_against_owner_mirror": format_checks(arr, mask, grid, sample_grid, foot),
        }
    if support is None or not support.any():
        raise ValueError("Empty candidate support")

    comparisons = {}
    for pin in [*pins["focus"], pins["lattice"]]:
        ref, _, ref_grid = load_grid(fetch_pin(pin, cache))
        if any(ref_grid[k] != sample_grid[k] for k in ("shape", "crs", "transform")):
            raise ValueError("Pinned reference grid differs from sample mirror")
        ref_dots = foot & np.isfinite(ref) & (ref > 0)
        if not ref_dots.any() or not np.all((ref[foot] == 0) | (ref[foot] == 1)):
            raise ValueError("Empty or non-binary registry reference")
        covered = ndimage.binary_dilation(ref_dots, structure=disk(3))
        matches, count, fraction = directional_overlap(support, covered)
        rho = binary_spearman(support, ref_dots, foot)
        comparisons[pin.get("site", "13GEMSDOE-lattice")] = {
            "reference_sha256": pin["sha256"],
            "matches_within_3px": matches,
            "candidate_positive_pixels": count,
            "within_3px_fraction": fraction,
            "binary_spearman_footprint": rho,
            "duplicate_stop": fraction is None or rho is None or fraction > .70 or rho > .90,
        }

    receipt = json.loads((ROOT / "evidence/run_card_final.json").read_text())
    score = receipt["holdout_dti"]
    return {
        "schema": "apartgems-parallel-candidate-audit-v1",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Read-only saved-byte/geometry audit; owner-mirrored sample is not organizer-authenticated. No model or holdout rerun; nine focus variants and a registered lattice are not the complete registry.",
        "sample_sha256": pins["sample"]["sha256"],
        "variants": variants,
        "comparisons": comparisons,
        "preplacement_surface_all_registry": "Not established by this review; the parallel receipt does not record a lattice surface comparison.",
        "literal_uniqueness": "FAIL: registered lattice exceeds the 70% within-three-pixels stop rule.",
        "parallel_holdout_report": {
            "source": "evidence/run_card_final.json",
            "label": "HOLDOUT-DTI, reported by parallel run; not independently reproduced",
            "evaluator_version": receipt["evaluator_version"],
            "withheld_positive_count": receipt["n_withheld_positives"],
            "point": score,
            "ci95": receipt["holdout_ci95"],
            "champion_foldlocal": receipt["champion_foldlocal_dti"],
            "paired_delta": receipt["paired_delta_vs_champion"],
        },
        "selection_or_portal_receipt": None,
        "verdict": "negative",
        "submission_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache/audit")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/parallel_candidate_audit.json")
    args = parser.parse_args()
    result = audit(args.cache)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    lattice = result["comparisons"]["13GEMSDOE-lattice"]
    print(f"Read-only audit: {lattice['within_3px_fraction']:.4%} lattice overlap; verdict negative; no submission.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
