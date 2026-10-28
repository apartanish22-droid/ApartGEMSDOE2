"""Regression coverage for the negative 2026-10-28 review (no real model runs)."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from gems32.release_gate import REQUIRED_VALIDATOR_CHECKS, compare_registry, promotion_decision

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import experiment_guard  # noqa: E402
import restore_data  # noqa: E402


def test_caller_assertions_cannot_promote():
    candidate = {"dti": 0.2, "ci95": [0.15, 0.25], "evaluator_version": "test", "n_withheld_positives": 10}
    incumbent = {"dti": 0.1, "ci95": [0.05, 0.15], "evaluator_version": "test", "n_withheld_positives": 10}
    result = promotion_decision(
        lane="asserted lane", surface_check={"stage": "surface", "passed": True},
        final_check={"stage": "final", "passed": True}, canary_aucs=[0.5],
        holdout=candidate, incumbent=incumbent, same_evaluation=True,
        validator={x: True for x in REQUIRED_VALIDATOR_CHECKS}, paired_delta_ci95=[0.01, 0.1],
    )
    assert all(value for key, value in result["gates"].items() if key != "independent_evidence_verified")
    assert not result["gates"]["independent_evidence_verified"]
    assert result["verdict"] == "negative"
    assert result["assertions_only"] and result["selector_required"] and not result["slot_used"]


def test_missing_promotion_evidence_is_negative():
    result = promotion_decision(
        lane=None, surface_check=None, final_check=None, canary_aucs=None,
        holdout=None, incumbent=None, same_evaluation=False, validator=None,
    )
    assert result["verdict"] == "negative"
    assert not any(result["gates"].values())


def test_array_subset_cannot_be_mistaken_for_complete_registry():
    rng = np.random.default_rng(42)
    surface = rng.random((10, 10))
    other = rng.random((10, 10))
    footprint = np.ones((10, 10), bool)
    reference_dots = np.zeros((10, 10), bool)
    reference_dots[1, 1] = True
    report = compare_registry(surface, None, footprint, {"r": (other, reference_dots)}, stage="surface")
    assert report["provided_subset_passed"]
    assert not report["registry_complete_verified"]
    assert not report["passed"] and report["stop"]
    constant = compare_registry(surface, None, footprint, {"r": (np.ones((10, 10)), reference_dots)}, stage="surface")
    assert not constant["provided_subset_passed"] and not constant["passed"]
    empty = compare_registry(surface, None, footprint, {}, stage="surface")
    assert not empty["provided_subset_passed"] and not empty["passed"]


def test_invalid_masks_cannot_be_silently_coerced():
    surface = np.arange(9).reshape(3, 3)
    footprint = np.ones((3, 3), int)
    footprint[0, 0] = 0
    dots = np.zeros((3, 3), float)
    dots[0, 0] = 1
    with pytest.raises(ValueError, match="inside the footprint"):
        compare_registry(surface, dots, footprint, {}, stage="final")
    dots[0, 0] = np.nan
    with pytest.raises(ValueError, match="dots must be binary"):
        compare_registry(surface, dots, footprint, {}, stage="final")
    with pytest.raises(ValueError, match="finite binary"):
        compare_registry(surface, None, np.full((3, 3), np.nan), {}, stage="surface")


def test_archive_guard_remains_blocked_even_if_preflight_changes(monkeypatch):
    # The guard intentionally ignores future READY assertions; a spent lane
    # needs a new independently reviewed implementation, not an unlocked flag.
    import preflight
    monkeypatch.setattr(preflight, "inspect", lambda: {"status": "READY", "new_experiment_authorized": True})
    assert experiment_guard.require_current_protocol() is False


@pytest.mark.parametrize("command", [
    ["scripts/run_trace_experiments.py"],
    ["scripts/emit_trace_deliverable.py"],
    ["scripts/build_rad_scarp_submission.py"],
    ["scripts/run_h_dil_grav_experiment.py"],
    ["scripts/run_h_mag_edge_slope_experiment.py"],
    ["scripts/run_h_depth_cond_experiment.py"],
    ["scripts/run_udsr_experiments.py"],
    ["scripts/emit_and_audit_deliverables.py"],
    ["scripts/run_ap2.py"],
    ["scripts/finalize_ap2.py"],
    ["scripts/run_experiment.py"],
    ["scripts/run_experiment_oof.py"],
    ["scripts/build_final.py"],
    ["src/generate_submission.py"],
    ["src/generate_h2_fractal_submission.py"],
])
def test_archived_entrypoints_stop_before_writes(command, tmp_path):
    downloads = ROOT / "docs/downloads"
    before = {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in downloads.iterdir() if p.is_file()}
    env = dict(os.environ, GEMS_DATA_DIR=str(tmp_path / "missing_data"), GEMS_WORK_DIR=str(tmp_path / "work"),
               OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    proc = subprocess.run([sys.executable, *command], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
    assert proc.returncode != 0
    assert "BLOCKED" in proc.stderr or "STOP:" in proc.stderr
    assert before == {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in downloads.iterdir() if p.is_file()}
    assert not (tmp_path / "work").exists()


def test_feature_rebuild_does_not_overwrite_receipt(tmp_path):
    receipt = tmp_path / "receipt.json"
    receipt.write_text("keep me")
    out = tmp_path / "stack.npy"
    proc = subprocess.run(
        [sys.executable, "scripts/build_features.py", "--out", str(out), "--receipt", str(receipt)],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
        env=dict(os.environ, GEMS_DATA_DIR=str(tmp_path / "missing"), OPENBLAS_NUM_THREADS="1"),
    )
    assert proc.returncode != 0 and "BLOCKED" in proc.stderr
    assert receipt.read_text() == "keep me" and not out.exists()
    assert "existing_faults" in restore_data.CORE_IDS


def test_current_card_and_split_receipt_are_consistent():
    card = json.loads((ROOT / "evidence/current_run_card.json").read_text())
    split = json.loads((ROOT / "evidence/shared_split_geometry_20261028.json").read_text())
    recheck = json.loads((ROOT / "evidence/trace_independent_recheck_20261028.json").read_text())
    assert card["verdict"] == "negative" and card["new_candidate"] is None
    assert card["experiments_run_this_review"] == card["weekly_slots_used_this_review"] == 0
    assert card["holdout_dti"]["current_valid_point"] is None
    assert split["withheld_positive_occurrences"] == 22232
    assert split["truth_occurrences_within_15px_of_visible"] == 15705
    assert split["partially_scored_component_instances"] == 76
    assert not split["all_truth_more_than_15px_from_visible"] and not split["all_components_wholly_scored"]
    assert split["shared_evaluator_sha256"] == hashlib.sha256((ROOT / split["shared_evaluator_file"]).read_bytes()).hexdigest()
    assert recheck["candidate_sha256"] == card["raster_sha256"]
    assert recheck["overlap_fraction"] == card["registry_correlation_overlap"]["final_dots_vs_lattice"]["fraction"]
    assert not recheck["literal_overlap_gate_pass"] and not recheck["outside_null_or_masked"]
    assert recheck["dtype"] == "float32"
    assert recheck["in_footprint_nan_cells"] == recheck["in_footprint_nonfinite_cells"] == recheck["in_footprint_masked_cells"] == 0
    assert len(card["submission"]["note"]) == card["submission"]["note_length"] <= 140
    assert not card["submission"]["upload_authorized"]
    assert card["organizer_confirmed_score"] is None and card["leaderboard_estimate"] is None
    rad = json.loads((ROOT / "evidence/rad_scarp_independent_recheck_20261028.json").read_text())
    rad_card = json.loads((ROOT / "evidence/rad_scarp_run_card_20261028.json").read_text())
    assert rad["candidate_dots_within_3px"] == card["concurrent_research_artifact"]["dots_near_lattice"] == 10421
    assert rad["candidate_positive_pixels_inside_mirror"] == 10457
    assert not rad["literal_overlap_gate_pass"] and not rad["outside_null_or_masked"]
    assert rad["dtype"] == "float32" and rad["in_footprint_nan_cells"] == rad["in_footprint_masked_cells"] == 0
    assert rad_card["unique_vs_gemsdoe_sites"] is None and not rad_card["validator_output"]["all_pass"]
    assert rad_card["verdict"] == "negative" and "not valid HOLDOUT-DTI" in rad_card["score_label"]
    three = json.loads((ROOT / "evidence/parallel_three_independent_recheck_20261028.json").read_text())
    assert not card["concurrent_parallel_three"]["registry_complete_verified"]
    assert [v["candidate_dots_within_3px"] for v in three["candidates"].values()] == [36692, 5098478, 5099871]
    assert all(not v["literal_overlap_gate_pass"] and not v["outside_null_or_masked"] for v in three["candidates"].values())
    for path in ("h_dil_grav_exp1_20261028T224631Z.json", "h_mag_edge_slope_exp2_20261028T224750Z.json", "h_depth_cond_exp3_20261028T224836Z.json"):
        def reject_nonstandard(value):
            raise ValueError(f"non-standard JSON: {value}")
        prior = json.loads((ROOT / "evidence" / path).read_text(), parse_constant=reject_nonstandard)
        assert prior["verdict"] == "negative" and not prior["validator_output"]["all_checks_passed"]
        assert "not valid HOLDOUT-DTI" in prior["score_label"]
        assert not prior["registry_correlation_overlap"]["literal_gate_pass"]
    for name in ("current_run_card.json", "shared_split_geometry_20261028.json", "trace_independent_recheck_20261028.json", "rad_scarp_independent_recheck_20261028.json", "parallel_three_independent_recheck_20261028.json"):
        assert (ROOT / "docs/data" / name).read_bytes() == (ROOT / "evidence" / name).read_bytes()


def test_trace_receipt_replays_when_inputs_are_restored():
    if not (ROOT / 'data/audit/lattice.tif').is_file() or not (ROOT / 'data/audit/mirror_sample.tif').is_file():
        pytest.skip('fetch pinned audit inputs for H-TRACE saved-byte replay')
    from recheck_trace import inspect_trace
    recorded = json.loads((ROOT / 'evidence/trace_independent_recheck_20261028.json').read_text())
    assert inspect_trace() == {k: v for k, v in recorded.items() if k != 'checked_utc'}
    from recheck_rad_scarp import inspect_rad_scarp
    recorded_rad = json.loads((ROOT / 'evidence/rad_scarp_independent_recheck_20261028.json').read_text())
    assert inspect_rad_scarp() == {k: v for k, v in recorded_rad.items() if k != 'checked_utc'}
    from recheck_parallel_three import inspect_parallel_three
    recorded_three = json.loads((ROOT / 'evidence/parallel_three_independent_recheck_20261028.json').read_text())
    assert inspect_parallel_three() == {k: v for k, v in recorded_three.items() if k != 'checked_utc'}


def test_publication_exposes_the_actual_blockers():
    home = (ROOT / 'docs/index.html').read_text()
    trace = (ROOT / 'docs/trace/index.html').read_text()
    assert '15,705' in home and '22,232' in home
    assert 'after' in home and 'dot placement' in home
    assert '99.857%' in home and 'DO NOT SUBMIT' in home
    assert 'not valid under the requested buffered-whole-segment protocol' in home
    assert 'not a complete pre-placement pass' in trace
    assert 'data/current_run_card.json' in home
    assert '10,421 / 10,457' in home and 'rad_scarp_independent_recheck_20261028.json' in home
    assert '99.23%, 99.903% and 99.872%' in home and 'parallel_three_independent_recheck_20261028.json' in home
    for page in (ROOT / 'docs/ap2').glob('*.html'):
        assert 'buffered whole-segment split' in page.read_text()
