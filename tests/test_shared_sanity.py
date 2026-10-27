"""Sanity-check the unmodified shared metric when restored locally."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[1] / 'data/shared_template/src/gems/metric.py'
pytestmark = pytest.mark.skipif(not PATH.exists(), reason='read-only upstream template has not been restored')


def metric():
    spec = importlib.util.spec_from_file_location('upstream_metric', PATH)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def test_exact_and_binary_match_simple_triangular_kernel():
    m = metric(); truth = np.zeros((9, 9)); truth[4, 4] = 1
    pred = np.zeros_like(truth); pred[4, 5] = 1
    exact = m.dti_components_exact(pred, truth)
    fast = m.dti_score_fast(pred, truth)
    assert exact['TP_w'] == pytest.approx(2/3)
    assert exact['FP_w'] == pytest.approx(1/3)
    assert exact['FN_w'] == pytest.approx(1/3)
    assert exact['dti'] == pytest.approx(2/3, abs=1e-6)
    assert fast['dti'] == pytest.approx(exact['dti'], abs=1e-8)


def test_soft_probability_and_pixel_exact_catalogue_mask():
    m = metric(); truth = np.zeros((9, 9)); truth[4, 4] = 1
    pred = np.zeros_like(truth); pred[4, 4] = .5
    assert m.dti_components_exact(pred, truth)['dti'] == pytest.approx(.5 / (.5 + .8*.5), abs=1e-6)
    known = np.zeros_like(truth, bool); known[4, 4] = True
    assert m.dti_components_exact(pred, truth, catalogue_mask=known)['n_truth'] == 0
