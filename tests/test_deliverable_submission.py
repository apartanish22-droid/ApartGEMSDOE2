"""End-to-end automated verification of the ApartGEMSDOE2 deliverable GeoTIFF, ZIP, Run Card,
shared-tool hashes, and GitHub Pages links (executes programmatically with zero human inspection).
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import rasterio

from gemsdoe32.submission import validate_submission_geotiff

ROOT = Path(__file__).resolve().parents[1]


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_promoted_geotiff_and_zip_strict_format_and_range():
    rc = json.loads((ROOT / "evidence/apartgemsdoe2_run_card_20261027.json").read_text())
    tif_path = ROOT / rc["artifact_paths"]["geotiff"]
    zip_path = ROOT / rc["artifact_paths"]["zip"]
    assert tif_path.is_file(), f"Missing deliverable GeoTIFF: {tif_path}"
    assert zip_path.is_file(), f"Missing deliverable ZIP: {zip_path}"

    # Verify exact SHA-256 match with Run Card
    tif_sha = _sha256(tif_path)
    assert tif_sha == rc["raster_sha256"]

    # Verify ZIP contains exactly ONE .tif with identical bytes (DrivenData zip rule)
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        assert len(names) == 1 and names[0] == tif_path.name
        zip_inner_sha = hashlib.sha256(zf.read(names[0])).hexdigest()
        assert zip_inner_sha == tif_sha

    # Verify GeoTIFF CRS, shape, geotransform, nodata, finite [0, 1] range
    with rasterio.open(tif_path) as ds:
        assert ds.count == 1
        assert str(ds.crs) == "EPSG:32611"
        assert ds.shape == (3730, 3292)
        assert tuple(ds.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        assert ds.nodata is None
        arr = ds.read(1)
        assert arr.dtype == np.float32
        assert np.isfinite(arr).all(), "GeoTIFF contains NaN or Inf!"
        assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0, "Values out of [0, 1]!"
        assert int((arr > 0.0).sum()) == 26173

    # When .cache/gems_data is hydrated, also run template & catalogue zero-overlap checks
    tpl = ROOT / ".cache/gems_data/sample_submission.tif"
    lbl = ROOT / ".cache/gems_data/labels.tif"
    if tpl.is_file() and lbl.is_file():
        rep = validate_submission_geotiff(tif_path, tpl, strict_whole_array_finite=True)
        assert rep.passed, f"Template validator failed: {rep.to_dict()}"
        with rasterio.open(lbl) as dsl:
            cat = dsl.read(1) > 0
        assert int(((arr > 0) & cat).sum()) == 0


def test_protocol_gates_canary_uniqueness_budget_and_runcard():
    rc = json.loads((ROOT / "evidence/apartgemsdoe2_run_card_20261027.json").read_text())
    required = {
        "hypothesis",
        "mechanism",
        "mimic_process",
        "holdout_dti",
        "ci",
        "registry_correlation_overlap",
        "raster_sha256",
        "validator_output",
        "submission_name",
        "note",
        "verdict",
    }
    assert required.issubset(rc.keys())
    assert len(rc["note"]) <= 140
    assert rc["verdict"] in {"promote", "negative"}
    assert rc["validator_output"]["passed"] is True
    assert rc["validator_output"]["values_in_0_1"] is True
    assert rc["validator_output"]["no_nan_inside_footprint"] is True

    # Leakage canary <= 0.90 across all 55 channels
    canary = json.loads((ROOT / "evidence/leakage_canary_55ch.json").read_text())
    assert canary["passed"] is True
    assert canary["n_features_tested"] == 55
    assert canary["max_oriented_auc"] <= 0.90

    # Duplication gate <= 0.90 surface Spearman & <= 0.70 sparse 3px dot overlap
    reg = rc["registry_correlation_overlap"]
    assert reg["passed"] is True
    assert reg["surface_max_abs_spearman"] <= 0.90
    assert reg["dots_max_sparse_within_3px_488"] <= 0.70
    assert reg["dots_within_3px_vs_gemsdoe32_b2"] <= 0.50

    # Strict <= 3 experiment budget
    exps = json.loads((ROOT / "evidence/udsr_three_experiments_20261027.json").read_text())
    assert exps["experiment_budget_used"] == 3
    assert len(exps["experiments"]) == 3


def test_shared_tool_hashes_and_docs_integrity():
    # Verify all 10 shared template files remain bit-identical to pinned hashes
    for line in (ROOT / "data/shared_tool_hashes.txt").read_text().splitlines():
        if not line.strip():
            continue
        expected_sha, rel_path = line.strip().split()
        assert _sha256(ROOT / rel_path) == expected_sha, f"Modified shared tool: {rel_path}"

    # Verify README contains Arena Core Values & zero score projections
    readme = (ROOT / "README.md").read_text()
    assert "Maximize P(Win)" in readme
    assert "Own the Outcome" in readme

    # Verify all local asset/download links in docs/ resolve cleanly and ban projections
    forbidden = re.compile(r"(projected\s+leaderboard\s+score|estimated\s+live\s+score\s*:)", re.I)
    for html_name in ("index.html", "executive-summary.html"):
        html_path = ROOT / "docs" / html_name
        assert html_path.is_file()
        txt = html_path.read_text()
        assert not forbidden.search(txt), f"Projection phrasing found in {html_name}"
        for m in re.finditer(r'(?:href|src)="([^"#]+)"', txt):
            ref = m.group(1)
            if ref.startswith(("http://", "https://", "mailto:")):
                continue
            target = (html_path.parent / ref).resolve()
            assert target.is_file() and target.stat().st_size > 0, f"Broken link in {html_name}: {ref}"
