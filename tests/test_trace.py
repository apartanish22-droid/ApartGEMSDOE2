"""Unit tests for the H-TRACE oriented trace-coherence transform."""
import numpy as np

from gems32 import trace


def _foot(shape=(61, 61)):
    return np.ones(shape, bool)


def test_line_scores_higher_than_speckle():
    rng = np.random.default_rng(0)
    field = (rng.random((61, 61), dtype=np.float32) * 0.05).astype(np.float32)
    field[30, 10:51] = 1.0          # continuous horizontal trace
    field[8, 8] = 1.0               # isolated speckle, same peak value
    out = trace.trace_coherence(field, _foot())
    assert out["t_geo"][30, 30] > 0.5
    assert out["t_geo"][8, 8] < 0.05
    # best orientation on the horizontal line is the (0, 1) step (index 0)
    assert out["theta_long"][30, 30] == 0


def test_diagonal_line_orientation():
    field = np.zeros((61, 61), dtype=np.float32)
    for k in range(10, 51):
        field[k, k] = 1.0
    out = trace.trace_coherence(field, _foot())
    assert out["t_geo"][30, 30] > 0.5
    assert out["theta_long"][30, 30] == 2   # (1, 1) step


def test_no_border_wraparound():
    field = np.zeros((41, 41), dtype=np.float32)
    field[20, :] = 1.0                       # line touching both borders
    out = trace.trace_coherence(field, _foot((41, 41)))
    # a corner far from the line must stay at zero (np.roll would leak)
    assert out["t_geo"][0, 0] == 0.0
    assert out["t_geo"][20, 20] > 0.5


def test_gate_field_floor_and_footprint():
    post = np.full((5, 5), 0.8, dtype=np.float32)
    tn = np.zeros((5, 5), dtype=np.float32)
    foot = _foot((5, 5))
    foot[0, 0] = False
    gated = trace.trace_gate_field(post, tn, foot, floor=0.2)
    assert np.isclose(gated[2, 2], 0.16)     # 0.8 * 0.2 floor when Tn = 0
    assert gated[0, 0] == 0.0
    tn[:] = 1.0
    gated = trace.trace_gate_field(post, tn, foot, floor=0.2)
    assert np.isclose(gated[2, 2], 0.8)      # full pass-through when Tn = 1


def test_hysteresis_bridges_small_gap_only_along_line():
    seeds = np.zeros((21, 41), bool)
    seeds[10, 5:18] = True
    seeds[10, 22:36] = True                  # 4-px gap at cols 18..21
    support = trace.hysteresis_support(seeds, _foot((21, 41)))
    assert support[10, 18:22].all()          # gap bridged along the line
    assert not support[2, 20]                # no isotropic blob growth
