"""Score-ordered greedy Poisson-disk emission (min separation in px) with catalogue collar.

Distinct from the incumbent raster-order `dot_thin` cascade (src/gems32/emission.py):
candidates are visited in descending surface score, so the field — not raster order —
decides the layout. A uniform grid hash keeps the min-distance test O(1) amortised.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt


def score_ordered_dots(surface: np.ndarray, foot: np.ndarray, labels: np.ndarray,
                       n_target: int = 37654, min_sep: float = 2.8, collar_px: float = 2.0,
                       pool: int = 600000, order_field: np.ndarray | None = None) -> np.ndarray:
    dcat = distance_transform_edt(~labels) if collar_px > 0 else None
    elig = foot.copy()
    if dcat is not None:
        elig &= dcat > collar_px
    key = (order_field if order_field is not None else surface).astype(np.float32)
    key = np.where(elig, key, -np.inf)
    flat = key.ravel()
    k = min(pool, int(elig.sum()))
    idx = np.argpartition(flat, -k)[-k:]
    idx = idx[np.argsort(-flat[idx], kind="mergesort")]
    H, W = surface.shape
    cell = float(min_sep)
    grid: dict[tuple[int, int], list[tuple[int, int]]] = {}
    out = np.zeros(surface.shape, dtype=bool)
    r2 = min_sep * min_sep
    accepted = 0
    for flat_i in idx:
        y, x = divmod(int(flat_i), W)
        cy, cx = int(y // cell), int(x // cell)
        ok = True
        for gy in range(cy - 2, cy + 3):
            for gx in range(cx - 2, cx + 3):
                for (ky, kx) in grid.get((gy, gx), ()):  # pragma: no branch
                    dy, dx = y - ky, x - kx
                    if dy * dy + dx * dx < r2:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            out[y, x] = True
            grid.setdefault((cy, cx), []).append((y, x))
            accepted += 1
            if accepted >= n_target:
                break
    if accepted < n_target:
        raise RuntimeError(f"emission pool exhausted: {accepted} < {n_target}")
    return out


def random_dots(foot: np.ndarray, labels: np.ndarray, n_target: int = 37654,
                min_sep: float = 2.8, collar_px: float = 2.0, seed: int = 20261027) -> np.ndarray:
    """Score-blind matched control: uniform random surface through the same emitter."""
    rng = np.random.default_rng(seed)
    surf = rng.random(foot.shape, dtype=np.float32)
    return score_ordered_dots(surf, foot, labels, n_target, min_sep, collar_px, pool=900000)
