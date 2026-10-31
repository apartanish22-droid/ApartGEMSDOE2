"""Recheck the prior H-BLIND-Conduit demo's footprint audit; never promote it."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
AUDIT = json.loads((ROOT / "evidence/h_blind_conduit_footprint_audit_20261031.json").read_text())
CARD = json.loads((ROOT / "evidence/h_blind_conduit_run_card.json").read_text())


def test_saved_demo_matches_audit_and_is_not_a_submission() -> None:
    candidate = ROOT / AUDIT["candidate"]["path"]
    proxy = ROOT / AUDIT["comparison_reference"]["path"]
    input_grid = ROOT / AUDIT["method_source_review"]["reference_path"]

    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == AUDIT["candidate"]["sha256"]
    assert hashlib.sha256(proxy.read_bytes()).hexdigest() == AUDIT["comparison_reference"]["sha256"]
    assert hashlib.sha256(input_grid.read_bytes()).hexdigest() == AUDIT["method_source_review"]["reference_sha256"]

    with rasterio.open(candidate) as c, rasterio.open(proxy) as p, rasterio.open(input_grid) as src:
        arr = c.read(1)
        proxy_arr = p.read(1)
        proxy_foot = np.isfinite(proxy_arr)
        src_arr = src.read(1)
        assert (c.crs, c.shape, c.transform) == (p.crs, p.shape, p.transform)
        assert c.count == 1 and c.dtypes[0] == "float32"
        assert np.isfinite(arr).all() and float(arr.min()) >= 0 and float(arr.max()) <= 1
        assert int((arr > 0).sum()) == AUDIT["candidate"]["positive_cells"] == 25000
        assert int(proxy_foot.sum()) == AUDIT["comparison_reference"]["finite_mask_pixels"] == 5167373
        assert np.isfinite(src_arr).all() and src.nodata is None
        assert int(np.isfinite(src_arr).sum()) == arr.size == 12279160
        inside = int(((arr > 0) & proxy_foot).sum())
        outside = int(((arr > 0) & ~proxy_foot).sum())

    assert inside == AUDIT["observed"]["candidate_positive_cells_inside_proxy_mask"] == 9013
    assert outside == AUDIT["observed"]["candidate_positive_cells_outside_proxy_mask"] == 15987
    assert AUDIT["observed"]["surface_rank_correlation_vs_complete_registry"] is None
    assert AUDIT["observed"]["final_dot_overlap_vs_complete_registry"] is None
    assert AUDIT["observed"]["holdout_dti"] is None
    assert CARD["ok_to_submit"] is False
    assert CARD["verdict"].startswith("negative")
    assert AUDIT["decision"].startswith("NEGATIVE")
