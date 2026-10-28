"""Archived/demo generators must not create new rasters or overwrite status."""
import hashlib
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('entrypoint', [
    'src/generate_h2_fractal_submission.py',
    'scripts/run_trace_experiments.py',
    'scripts/emit_trace_deliverable.py',
    'scripts/run_udsr_experiments.py',
    'scripts/emit_and_audit_deliverables.py',
    'scripts/run_experiment.py', 'scripts/run_experiment_oof.py', 'scripts/build_final.py',
    'scripts/run_ap2.py', 'scripts/finalize_ap2.py',
])
def test_archived_entrypoint_stops_before_writing(entrypoint):
    before_files = {p.name for p in (ROOT/'docs/downloads').glob('*')}
    paths = [ROOT/'assets/SUBMISSION_STATUS.txt', ROOT/'evidence/trace_run_card_20261028.json',
             ROOT/'evidence/trace_three_experiments_20261028.json']
    before_hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    proc = subprocess.run([sys.executable, str(ROOT/entrypoint)], cwd=ROOT,
                          capture_output=True, text=True, timeout=20)
    assert proc.returncode != 0
    assert 'BLOCKED' in proc.stderr
    assert {p.name for p in (ROOT/'docs/downloads').glob('*')} == before_files
    assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths] == before_hashes


@pytest.mark.parametrize('entrypoint', [
    'scripts/run_trace_experiments.py', 'scripts/emit_trace_deliverable.py',
    'scripts/run_udsr_experiments.py', 'scripts/emit_and_audit_deliverables.py',
    'scripts/run_experiment.py', 'scripts/run_experiment_oof.py', 'scripts/build_final.py',
    'scripts/run_ap2.py', 'scripts/finalize_ap2.py',
])
def test_archived_runner_stays_blocked_even_if_preflight_is_changed(entrypoint):
    code = ("import sys,runpy; sys.path.insert(0, 'scripts'); import experiment_guard; "
            "experiment_guard.require_current_protocol=lambda: True; "
            f"runpy.run_path({entrypoint!r}, run_name='__main__')")
    proc = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True, timeout=20)
    assert proc.returncode != 0
    assert 'BLOCKED: archived' in proc.stderr
