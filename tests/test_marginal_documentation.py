"""The multi-truth marginal identity is not the isolated-dot shortcut."""
import numpy as np
import pytest
from gems32.metric import components, dti


def test_one_dot_can_credit_multiple_truth_pixels():
    truth = np.zeros((9, 9), dtype=bool)
    truth[4, 3:6] = True
    before = np.zeros((9, 9))
    after = before.copy()
    after[4, 4] = 1
    a = components(before, truth)
    b = components(after, truth)
    delta_t = b['TP_w'] - a['TP_w']
    delta_fp = b['FP_w'] - a['FP_w']
    assert delta_t == pytest.approx(7 / 3)  # nearest-truth kernel is only 1
    assert delta_fp == pytest.approx(0)
    d0 = a['TP_w'] + .2*a['FP_w'] + .8*a['FN_w'] + 1e-12
    d1 = b['TP_w'] + .2*b['FP_w'] + .8*b['FN_w'] + 1e-12
    assert d1 - d0 == pytest.approx(.2 * (delta_t + 1 - 1))
    assert (dti(b['TP_w'], b['FP_w'], b['FN_w']) > dti(a['TP_w'], a['FP_w'], a['FN_w'])) == (delta_t > dti(a['TP_w'], a['FP_w'], a['FN_w']) * (d1 - d0))
