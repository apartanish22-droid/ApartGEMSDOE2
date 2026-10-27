import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_parallel_experiment_entrypoints_fail_before_emission():
    for script in ('run_experiment.py', 'run_experiment_oof.py', 'build_final.py'):
        result = subprocess.run([sys.executable, str(ROOT/'scripts'/script)], cwd=ROOT,
                                capture_output=True, text=True)
        assert result.returncode != 0, script
        assert 'BLOCKED' in result.stderr and 'no new experiment' in result.stderr.lower()


def test_recorded_parallel_candidate_fails_literal_rule():
    audit = json.loads((ROOT/'evidence/parallel_candidate_audit.json').read_text())
    lattice = audit['comparisons']['13GEMSDOE-lattice']
    assert lattice['within_3px_fraction'] > 0.70
    assert lattice['duplicate_stop'] is True
    assert audit['verdict'] == 'negative' and not audit['submission_authorized']
    assert audit['preplacement_surface_all_registry'].startswith('Not established')
    for item in audit['variants'].values():
        import hashlib
        h = hashlib.sha256((ROOT / item['file']).read_bytes()).hexdigest()
        assert h == item['sha256']
    assert not audit['variants']['zeros']['format_against_owner_mirror']['outside_null_or_masked']
    assert audit['variants']['nan']['format_against_owner_mirror']['outside_null_or_masked']


def test_pages_workflow_deploys_without_pushing_to_any_branch():
    workflow = (ROOT/'.github/workflows/source-feed.yml').read_text()
    assert 'actions/deploy-pages@v4' in workflow
    assert 'actions/upload-pages-artifact@v3' in workflow
    assert 'git push' not in workflow
    assert '--previous-url' in workflow and '/docs/data/source_feed.json' in workflow
    assert 'scripts/package_pages.py' in workflow
