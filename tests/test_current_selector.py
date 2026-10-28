"""The local selector is evidence-only; missing provenance never promotes."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from current_selector import REQUIRED_VALIDATOR_CHECKS, promotion_decision

SHA_REGISTRY, SHA_RASTER, SHA_EVALUATOR, SHA_FOLDS = ('a'*64, 'b'*64, 'c'*64, 'd'*64)


def evidence():
    auth = {'status': 'READY', 'new_experiment_authorized': True,
            'lane_assigned': True, 'assigned_lane': 'synthetic-test',
            'complete_parallel_registry': True, 'template_origin_authenticated': True,
            'registry_snapshot_sha256': SHA_REGISTRY, 'expected_feature_ids': ['terrain', 'magnetics']}
    audit = {'passed': True, 'audit_complete': True, 'registry_snapshot_sha256': SHA_REGISTRY,
             'registry_files_hash_verified': True,
             'registry_rasters': 3, 'malformed_or_missing': 0, 'constant_or_empty': 0,
             'worst_abs_spearman': 0.9}
    surface = dict(audit, stage='surface_before_placement')
    final = dict(audit, stage='final_dots', literal_rule_passed=True,
                 rank_basis='saved_final_dots', worst_within_3px_fraction=0.7,
                 candidate_raster_sha256=SHA_RASTER)
    record = {'evaluator_version': 'synthetic', 'evaluator_sha256': SHA_EVALUATOR,
              'fold_assignment_sha256': SHA_FOLDS, 'fold_local_visible_only': True,
              'zero_truth_fp_reconciled': True, 'n_withheld_positives': 8,
              'dti': 0.2, 'ci95': [0.1, 0.3]}
    return {'lane': 'synthetic-test', 'surface_check': surface, 'final_check': final,
            'canary_aucs': [0.6, 0.7], 'tested_feature_ids': ['terrain', 'magnetics'],
            'holdout': dict(record, dti=0.25), 'incumbent': record, 'same_evaluation': True,
            'validator': {**{k: True for k in REQUIRED_VALIDATOR_CHECKS}, 'raster_sha256': SHA_RASTER},
            'paired_delta_ci95': [0.01, 0.07], 'preflight': auth}


def test_only_complete_synthetic_evidence_can_reach_preselection():
    result = promotion_decision(**evidence())
    assert result['verdict'] == 'promote'
    assert not result['slot_approved']  # separate selector, never a submission


def test_array_only_or_legacy_boolean_receipts_cannot_promote():
    value = evidence()
    value['surface_check'] = {'stage': 'surface', 'passed': True}
    value['final_check'] = {'stage': 'final', 'passed': True}
    result = promotion_decision(**value)
    assert result['verdict'] == 'negative' and not result['slot_approved']


def test_cli_ignores_a_forged_preflight_and_never_spends_a_slot(tmp_path):
    path = tmp_path / 'receipt.json'
    path.write_text(json.dumps(evidence()))  # includes a forged READY preflight
    script = Path(__file__).resolve().parents[1] / 'scripts/check_candidate_evidence.py'
    result = subprocess.run([sys.executable, str(script), str(path)], capture_output=True, text=True)
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report['verdict'] == 'negative' and not report['slot_approved']
    assert any('current automated preflight' in issue for issue in report['issues'])


@pytest.mark.parametrize('change', [
    lambda e: e.update(preflight=None),
    lambda e: e['preflight'].update(assigned_lane='other'),
    lambda e: e['preflight'].update(complete_parallel_registry=False),
    lambda e: e['preflight'].update(template_origin_authenticated=False),
    lambda e: e['surface_check'].update(audit_complete=False),
    lambda e: e['surface_check'].update(malformed_or_missing=1),
    lambda e: e['surface_check'].update(registry_files_hash_verified=False),
    lambda e: e['surface_check'].update(worst_abs_spearman=0.901),
    lambda e: e['final_check'].update(literal_rule_passed=False),
    lambda e: e['final_check'].update(rank_basis='preplacement_surface'),
    lambda e: e['final_check'].update(worst_within_3px_fraction=0.701),
    lambda e: e['final_check'].update(registry_snapshot_sha256='e'*64),
    lambda e: e['final_check'].update(candidate_raster_sha256='e'*64),
    lambda e: e['final_check'].update(registry_rasters=2),
    lambda e: e.update(tested_feature_ids=['terrain']),
    lambda e: e.update(canary_aucs=[0.05, 0.7]),  # inverted leakage is also suspicious
    lambda e: e['holdout'].update(fold_local_visible_only=False),
    lambda e: e['holdout'].update(zero_truth_fp_reconciled=False),
    lambda e: e['incumbent'].update(fold_assignment_sha256='e'*64),
    lambda e: e['incumbent'].update(n_withheld_positives=7),
    lambda e: e.update(paired_delta_ci95=[0, 0.1]),
    lambda e: e['validator'].update(outside_null_or_masked=False),
    lambda e: e['validator'].update(raster_sha256=None),
])
def test_missing_or_conflicting_evidence_blocks_promotion(change):
    value = deepcopy(evidence()); change(value)
    result = promotion_decision(**value)
    assert result['verdict'] == 'negative'
    assert not result['slot_approved'] and result['issues']
