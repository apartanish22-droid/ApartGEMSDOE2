"""H-TRACE: oriented line-integral trace coherence for fault-trace emission fields.

Pre-registered in ``knowledge/preregistration_trace_20261028.md`` (session
``arena/7ec4400f-apartgemsdoe2``).  The transform reshapes a pixelwise posterior
field by requiring km-scale collinear support: for each of 8 orientations it
computes, along the segment through every pixel,

* ``line_mean``    -- mean field value along the segment, and
* ``support_frac`` -- fraction of segment pixels whose field value reaches a
  label-free low threshold ``tau`` (a footprint quantile of the field itself),

and scores the orientation by ``line_mean * support_frac``.  The best
orientation wins.  An isolated speckle has ``support_frac ~ 1/L`` and a diluted
``line_mean``, so its coherence collapses; a continuous trace keeps both high.
Two scales (segment half-lengths 7 px = 1.5 km and 15 px = 3.1 km at 100 m/px)
are combined by geometric mean.

All shifts use zero-padded slicing (never ``np.roll``), so no energy wraps
across image borders.  Fields are float32; peak extra memory is a handful of
full-frame float32 arrays (~50 MB each on the 3730x3292 grid).
"""
from __future__ import annotations

import numpy as np

# 8 orientations as unit-ish steps (dy, dx).  Steps of 2 in one axis give
# ~26.6 deg / ~63.4 deg orientations; intermediate pixels are sampled every
# step, which is the same convention as ``mdrc.directional_chain_max``.
ORIENTATIONS: tuple[tuple[int, int], ...] = (
    (0, 1), (1, 0), (1, 1), (1, -1), (2, 1), (1, 2), (2, -1), (1, -2),
)

HALF_SHORT_PX = 7    # 15-sample segment ~1.5 km
HALF_LONG_PX = 15    # 31-sample segment ~3.1 km


def _padded(field: np.ndarray, half: int) -> tuple[np.ndarray, int]:
    """Zero-pad so that any orientation step * half stays inside the array."""
    pad = 2 * half + 2
    return np.pad(field, pad, mode="constant"), pad


def _shift_view(padded: np.ndarray, pad: int, shape: tuple[int, int],
                dy: int, dx: int) -> np.ndarray:
    h, w = shape
    return padded[pad + dy: pad + dy + h, pad + dx: pad + dx + w]


def oriented_line_stats(field: np.ndarray, foot: np.ndarray, half: int,
                        tau: float) -> tuple[np.ndarray, np.ndarray]:
    """Best-orientation (coherence, orientation index) at one segment scale.

    ``coherence = max_theta line_mean_theta * support_frac_theta`` where the
    segment samples ``field`` at ``k * (dy, dx)`` for ``k in [-half, half]``
    and ``support_frac`` counts samples with value ``>= tau``.  The returned
    orientation index is the argmax orientation (for hysteresis closing).
    Outside ``foot`` the coherence is 0.
    """
    f = np.where(foot & np.isfinite(field), field, 0.0).astype(np.float32)
    fp, pad = _padded(f, half)
    bp, _ = _padded((f >= tau).astype(np.float32), half)
    n = float(2 * half + 1)
    best = np.zeros(f.shape, dtype=np.float32)
    best_theta = np.zeros(f.shape, dtype=np.int8)
    for ti, (dy, dx) in enumerate(ORIENTATIONS):
        ssum = np.zeros(f.shape, dtype=np.float32)
        bsum = np.zeros(f.shape, dtype=np.float32)
        for k in range(-half, half + 1):
            ssum += _shift_view(fp, pad, f.shape, k * dy, k * dx)
            bsum += _shift_view(bp, pad, f.shape, k * dy, k * dx)
        coh = (ssum / n) * (bsum / n)
        better = coh > best
        best[better] = coh[better]
        best_theta[better] = ti
    best[~foot] = 0.0
    return best, best_theta


def trace_coherence(field: np.ndarray, foot: np.ndarray,
                    tau_quantile: float = 0.90) -> dict:
    """Two-scale geometric-mean trace coherence plus per-scale diagnostics.

    ``tau`` is the ``tau_quantile`` footprint quantile of ``field`` itself
    (label-free).  Returns float32 maps ``t_short``, ``t_long``, ``t_geo``
    (geometric mean) and ``theta_long`` (int8 best orientation at long scale),
    plus the scalar ``tau`` used.
    """
    vals = field[foot & np.isfinite(field)]
    tau = float(np.quantile(vals[::4], tau_quantile)) if vals.size else 0.0
    t_short, _ = oriented_line_stats(field, foot, HALF_SHORT_PX, tau)
    t_long, theta_long = oriented_line_stats(field, foot, HALF_LONG_PX, tau)
    t_geo = np.sqrt(np.maximum(t_short, 0.0) * np.maximum(t_long, 0.0)).astype(np.float32)
    t_geo[~foot] = 0.0
    return {"t_short": t_short, "t_long": t_long, "t_geo": t_geo,
            "theta_long": theta_long, "tau": tau}


def normalise_p995(coherence: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Clip-normalise a coherence map to [0, 1] by its footprint p99.5."""
    vals = coherence[foot]
    scale = float(np.percentile(vals[::4], 99.5)) if vals.size else 0.0
    if scale <= 0.0:
        return np.zeros(coherence.shape, dtype=np.float32)
    out = np.clip(coherence / scale, 0.0, 1.0).astype(np.float32)
    out[~foot] = 0.0
    return out


def trace_gate_field(posterior: np.ndarray, coherence_norm: np.ndarray,
                     foot: np.ndarray, floor: float = 0.2) -> np.ndarray:
    """EXP-2 field: ``F0 * (floor + (1-floor) * Tn)`` inside the footprint."""
    f0 = np.where(foot & np.isfinite(posterior), posterior, 0.0).astype(np.float32)
    gate = (floor + (1.0 - floor) * np.clip(coherence_norm, 0.0, 1.0)).astype(np.float32)
    return (f0 * gate * foot).astype(np.float32)


def _oriented_closing(mask: np.ndarray, dy: int, dx: int, half: int = 2) -> np.ndarray:
    """Binary closing of ``mask`` with a (2*half+1)-sample line along (dy, dx).

    Closing = erosion of dilation; implemented with the same zero-padded
    shift machinery, bridging gaps of up to ``2*half`` samples along the line.
    """
    m = mask.astype(bool)
    mp, pad = _padded(m.astype(np.uint8), half)
    dil = np.zeros(m.shape, dtype=bool)
    for k in range(-half, half + 1):
        dil |= _shift_view(mp, pad, m.shape, k * dy, k * dx) > 0
    dp, pad = _padded(dil.astype(np.uint8), half)
    ero = np.ones(m.shape, dtype=bool)
    for k in range(-half, half + 1):
        ero &= _shift_view(dp, pad, m.shape, k * dy, k * dx) > 0
    return ero | m


def hysteresis_support(seed_mask: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """EXP-3 support: union over orientations of oriented closings of seeds."""
    support = np.asarray(seed_mask, bool) & foot
    for dy, dx in ORIENTATIONS:
        support |= _oriented_closing(seed_mask & foot, dy, dx, half=2)
    return support & foot
