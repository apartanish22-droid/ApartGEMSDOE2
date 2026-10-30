"""Verification of the H-RIDGE3 candidate: DTI implementation, file bytes and recorded gates.

The DTI implementation inside scripts/generate_ridge_tensor_candidate.py is cross-checked against
the repo's literal brute-force transcription in src/gems32/metric.py (dti_bruteforce).
"""
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32 import metric as M  # noqa: E402

G = importlib.import_module("generate_ridge_tensor_candidate")

RUN_CARD = ROOT / "evidence/ridge3_run_card_20261030.json"
NINE = ROOT / "evidence/nine_site_bests_20261030.json"
NAN_TIF = ROOT / "docs/downloads/apartgemsdoe2-h-ridge3-tensorfuse-37654-20261030-nan.tif"
ZERO_TIF = ROOT / "docs/downloads/apartgemsdoe2-h-ridge3-tensorfuse-37654-20261030-zeros.tif"


def _components_on_grid(pred, truth):
    rows, cols = np.nonzero(truth)
    return G.dtw_components(pred, rows, cols, np.ones(pred.shape, bool))


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_dtw_matches_repo_bruteforce_on_random_grids(seed):
    rng = np.random.default_rng(seed)
    pred = np.where(rng.random((24, 24)) < 0.08, rng.random((24, 24)), 0.0)
    truth = rng.random((24, 24)) < 0.05
    if not truth.any() or not (pred > 0).any():
        pytest.skip("degenerate random draw")
    ours = _components_on_grid(pred, truth)
    ref = M.dti_bruteforce(pred, truth)
    assert ours["TP_w"] == pytest.approx(ref["tp"], rel=1e-9, abs=1e-9)
    assert ours["FP_w"] == pytest.approx(ref["fp"], rel=1e-9, abs=1e-9)
    assert ours["FN_w"] == pytest.approx(ref["fn"], rel=1e-9, abs=1e-9)
    assert ours["DTI"] == pytest.approx(ref["dti"], rel=1e-9, abs=1e-9)


def test_hand_worked_example_one_pixel_off_truth():
    # One truth pixel; one prediction at distance 1 px with p = 1.
    # k(1) = 2/3  => TP_w = 2/3, FP_w = 1 * (1 - 2/3) = 1/3, FN_w = 1 - 2/3 = 1/3
    # DTI = (2/3) / (2/3 + 0.2 * 1/3 + 0.8 * 1/3) = 2/3
    pred = np.zeros((9, 9))
    truth = np.zeros((9, 9), bool)
    truth[4, 4] = True
    pred[4, 5] = 1.0
    out = _components_on_grid(pred, truth)
    assert out["TP_w"] == pytest.approx(2 / 3)
    assert out["FP_w"] == pytest.approx(1 / 3)
    assert out["FN_w"] == pytest.approx(1 / 3)
    assert out["DTI"] == pytest.approx(2 / 3)


def test_perfect_and_empty_predictions():
    truth = np.zeros((9, 9), bool)
    truth[2, 2] = truth[6, 6] = True
    perfect = truth.astype(float)
    assert _components_on_grid(perfect, truth)["DTI"] == pytest.approx(1.0)
    empty = np.zeros((9, 9))
    assert _components_on_grid(empty, truth)["DTI"] == pytest.approx(0.0, abs=1e-9)


def test_run_card_records_the_gates_as_reported():
    card = json.loads(RUN_CARD.read_text())
    g = card["gates"]
    assert g["G1_pass"] is True
    assert g["G1_surface_max_abs_spearman"] <= 0.90
    assert g["G2_pass_literal"] is False          # reported as failing, not exempted
    assert g["G2_pass_excluding_lattice"] is True  # exclusion is a user decision, shown separately
    assert g["G2_dots_max_within_3px_excluding_lattice"] <= 0.70
    assert g["G3_format_pass"] is True
    assert card["inputs"]["labels_used_for_generation"] is False
    assert card["holdout_dti"] is None
    assert card["organizer_confirmed_score"] is None
    assert card["leaderboard_estimate"] is None


def test_candidate_files_match_run_card_hashes_and_format():
    card = json.loads(RUN_CARD.read_text())
    if not NAN_TIF.exists():
        pytest.skip("candidate raster not present")
    assert G.sha256(NAN_TIF) == card["output"]["sha256"]
    assert G.sha256(ZERO_TIF) == card["zeros_twin_readback"]["sha256"]
    import rasterio
    with rasterio.open(NAN_TIF) as ds:
        a = ds.read(1)
        assert ds.count == 1 and ds.dtypes[0] == "float32"
        assert ds.crs.to_epsg() == 32611
        assert (ds.height, ds.width) == (3730, 3292)
        assert tuple(ds.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        finite = np.isfinite(a)
        assert int(finite.sum()) == 5167373          # footprint cells carry values
        assert np.all((a[finite] >= 0) & (a[finite] <= 1))
        assert int((a[finite] > 0).sum()) == 37654   # candidate dots
    with rasterio.open(ZERO_TIF) as ds:
        b = ds.read(1)
        assert np.all(np.isfinite(b)) and np.all((b >= 0) & (b <= 1))


def test_nine_site_audit_records_duplicate_status_as_measured():
    data = json.loads(NINE.read_text())
    sites = {s["site"]: s for s in data["sites"]}
    assert set(sites) == {"GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
                          "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"}
    for s in sites.values():
        assert s["literal_unique_vs_other_sites"] is False
        assert s["max_overlap_other_site_nonlattice"] > 0.70
        assert s["max_overlap_calibration_lattice"] > 0.99
    assert sites["GEMSDOE32"]["user_reported_score"] == pytest.approx(0.2778)
    assert len(data["registry_duplicate_byte_groups"]) == 13


def test_independent_recheck_reproduces_run_card_under_strict_convention():
    rc = ROOT / "evidence/review_pass1_recheck_20261030.json"
    receipt = json.loads(rc.read_text())
    card = json.loads(RUN_CARD.read_text())["gates"]
    assert receipt["candidate_sha256"] == json.loads(RUN_CARD.read_text())["output"]["sha256"]
    assert receipt["lattice_overlap_strict_lt3"] == pytest.approx(card["G2_dots_max_within_3px_literal"])
    assert receipt["max_nonlattice_strict_lt3"]["fraction"] == pytest.approx(card["G2_dots_max_within_3px_excluding_lattice"])
    # inclusive convention is more conservative but leaves both verdicts unchanged
    assert receipt["lattice_overlap_inclusive_le3"] > 0.70
    assert receipt["max_nonlattice_inclusive_le3"]["fraction"] < 0.70


def test_decision_table_covers_every_candidate_and_blocks_upload():
    data = json.loads((ROOT / "evidence/submission_decision_20261030.json").read_text())
    rows = data["rows"]
    # 1 H-RIDGE3 + 3 candidates from main (v4, PR #38 blind-conduit, H-RAD-MAG-CONTRAST) + 9 site bests
    assert len(rows) == 13
    assert all(r["ok_to_submit"] == "NO" for r in rows)
    assert data["decision"] == "DO NOT UPLOAD ANY FILE YET"
    xc = json.loads((ROOT / "evidence/review_pass2_cross_candidates_20261030.json").read_text())["candidates"]
    assert xc["h-ridge3-nan"]["max_lattice_strict_lt3"]["fraction"] > 0.70
    assert xc["unique-blind-conduit-nan"]["max_lattice_strict_lt3"]["fraction"] > 0.70
    assert xc["v4-ridge-q5pct"]["max_lattice_strict_lt3"]["fraction"] > 0.70
