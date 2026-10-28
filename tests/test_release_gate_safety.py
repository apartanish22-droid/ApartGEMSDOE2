"""Known defects in the unchanged upstream copy; hard stops live at the runners.

Strict xfails are executable issue reproducers, not a private replacement for a
shared gate. When an upstream fix is available, repin it and remove the xfail.
"""
import hashlib
from pathlib import Path

import numpy as np
import pytest

from gems32.release_gate import REQUIRED_VALIDATOR_CHECKS, compare_registry, promotion_decision

ROOT = Path(__file__).resolve().parents[1]


def test_shared_sources_remain_byte_identical_to_upstream_pins():
    pinned = {
        'src/gems32/release_gate.py': 'ebf5bd483e84234ceb885070a1e717892f921d52112c0af52ffcd41f392ebebd',
        'src/gems32/registry_audit.py': 'f12b539c147e785a92e808b303e93fafef714c6f54591a73fde257524bc530ab',
    }
    for path, expected in pinned.items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected


def arguments(canaries):
    incumbent = dict(evaluator_version='v1', n_withheld_positives=40, dti=.1, ci95=[.09, .11])
    candidate = dict(incumbent, dti=.18, ci95=[.17, .19])
    return dict(lane='example', surface_check={'stage': 'surface', 'passed': True},
                final_check={'stage': 'final', 'passed': True}, canary_aucs=canaries,
                holdout=candidate, incumbent=incumbent, same_evaluation=True,
                validator={k: True for k in REQUIRED_VALIDATOR_CHECKS}, paired_delta_ci95=[.03, .1])


@pytest.mark.xfail(strict=True, reason='shared final-stage rank still uses pre-placement surface')
def test_final_rank_uses_actual_final_dots():
    foot = np.ones((20, 20), bool)
    dots = np.zeros_like(foot); dots[::3, ::3] = True
    surface = np.arange(400).reshape(20, 20).astype(float)
    result = compare_registry(surface, dots, foot, {'reference': (dots.astype(float), dots)}, stage='final')
    assert result['comparisons'][0]['spearman'] > .99


@pytest.mark.xfail(strict=True, reason='shared canary check misses inversely oriented AUC')
def test_inverse_canary_cannot_pass():
    assert promotion_decision(**arguments([.05]))['gates']['canaries'] is False


@pytest.mark.xfail(strict=True, reason='shared gate trusts bare passed flags and no provenance')
def test_bare_flags_and_incomplete_provenance_cannot_promote():
    assert promotion_decision(**arguments([.6]))['verdict'] == 'negative'
