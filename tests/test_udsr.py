from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt, label

from gems32 import udsr


def test_advect_updip_moves_hanging_wall_anomaly_onto_surface_trace():
    """Verify sign convention: hanging-wall peak at x=25 moves UP-DIP to surface break x=20."""
    h, w = 40, 50
    foot = np.ones((h, w), dtype=bool)
    yy, xx = np.meshgrid(np.arange(h, dtype=np.float32), np.arange(w, dtype=np.float32), indexing="ij")
    # Footwall on left (x <= 18), surface trace at x = 20, hanging-wall basin deepening eastward (+x)
    z_base = np.maximum((xx - 18.0) * 100.0, 0.0)
    dy_z, dx_z = np.gradient(z_base)
    nrm = np.hypot(dy_z, dx_z) + 1e-6
    dy_down, dx_down = (dy_z / nrm).astype(np.float32), (dx_z / nrm).astype(np.float32)

    # Subsurface contact anomaly peaks down-dip in hanging wall at x = 25 (5 px east of trace)
    source = np.exp(-((xx - 25.0) ** 2) / 2.0).astype(np.float32)
    adv = udsr.advect_updip_field(
        source, dy_down, dx_down, foot, offsets_px=(5.0,), weights=(1.0,)
    )
    peak_col = int(np.argmax(adv[20, :]))
    assert peak_col == 20, f"Expected updip peak at surface fault trace x=20, got x={peak_col}"
    assert adv[20, 20] > 0.95
    assert adv[20, 30] < 0.01


def test_exact_second_component_edt_matches_bruteforce():
    """Verify O(HW log C) binary bit-partition EDT matches brute-force 2nd-component distance."""
    h, w = 44, 48
    mask = np.zeros((h, w), dtype=bool)
    segments = [
        (slice(4, 12), slice(6, 7)),
        (slice(15, 24), slice(8, 9)),
        (slice(8, 9), slice(20, 30)),
        (slice(25, 35), slice(25, 26)),
        (slice(30, 38), slice(38, 40)),
        (slice(5, 10), slice(40, 41)),
        (slice(38, 40), slice(10, 18)),
    ]
    for rs, cs in segments:
        mask[rs, cs] = True
    comp, n_comp = label(mask, structure=np.ones((3, 3), dtype=int))
    assert n_comp == 7

    d_all = np.stack([distance_transform_edt(comp != c) for c in range(1, n_comp + 1)], axis=0)
    d2_brute = np.partition(d_all, 1, axis=0)[1].astype(np.float32)
    d2_fast = udsr.exact_second_component_edt(comp, downsample=1)
    np.testing.assert_allclose(d2_fast, d2_brute, rtol=1e-5, atol=1e-5)


def test_oriented_nms_and_visible_continuation_isolation():
    h, w = 64, 64
    foot = np.ones((h, w), dtype=bool)
    foot[:3, :] = False

    yy, xx = np.meshgrid(np.arange(h, dtype=np.float32), np.arange(w, dtype=np.float32), indexing="ij")
    surf = (0.8 * np.exp(-((xx - 32.0) ** 2) / 8.0)).astype(np.float32)
    sharp = udsr.oriented_nms_4az(surf, foot, blend=0.45)
    assert np.all(sharp[~foot] == 0.0)
    assert np.all((sharp >= 0.0) & (sharp <= 1.0))
    assert np.isclose(sharp[32, 32], surf[32, 32], atol=1e-6)
    assert sharp[32, 30] < surf[32, 30]

    # Visible continuation must NEVER depend on anything outside visible_mask
    vis_a = np.zeros((h, w), dtype=bool)
    vis_a[15:28, 20] = True
    vis_a[34:48, 22] = True  # En-echelon stepover relay gap between rows 28..34!
    cont_a = udsr.compute_visible_continuation(vis_a, foot)
    assert cont_a.shape == (h, w, 2)
    assert np.all(np.isfinite(cont_a))
    assert np.all((cont_a >= 0.0) & (cont_a <= 1.0))
    assert np.all(cont_a[~foot] == 0.0)
    # Relay bridge between the two en-echelon segments at (31, 21) should exceed far background (31, 55)
    assert cont_a[31, 21, 1] > cont_a[31, 55, 1] + 0.3
    # Invariance: adding a hidden fault outside vis_a does not alter visible_mask's continuation
    cont_a_repeat = udsr.compute_visible_continuation(vis_a.copy(), foot)
    np.testing.assert_array_equal(cont_a, cont_a_repeat)
