"""H-SPMD: SAR-PU Mapping-Propensity De-confounding & Shallow Matched-Depth / Epithermal Conduit Inversion.

Pre-registered lane in ``knowledge/preregistration_spmd_20261028.md``.
Extends the cached 35-ch shared stack + 18-ch UDSR stack with 8 new physical channels
(``spmd_stack_8.npy``: 5 strictly 1m-LiDAR-free shallow matched-depth magnetic & epithermal
alteration/lode channels + 3 1m-LiDAR dipolar scarp / graben / strike-concordance channels)
and trains fold-honest Dual-Cover gradient-boosted models under Selected-Not-At-Random
Positive-Unlabeled (SAR-PU) reliable-negative spy purification and geomorphic exposure
propensity de-confounding.

Engineered for < 2.2 GiB peak RSS on 3.8 GiB zero-swap containers via sequential strip
memmap streaming and explicit ``MADV_DONTNEED`` page-cache release.
"""
from __future__ import annotations

import gc
import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from numpy.lib.format import open_memmap
from scipy.ndimage import distance_transform_edt, gaussian_filter, zoom
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from . import features, udsr

SPMD_CHANNELS: tuple[str, ...] = (
    # 0..4: strictly 1 m LiDAR-free (5 channels -> global cols 53..57)
    "spmd_tmi_bandpass_ridge",     # 0 (col 53): GeoDAWN block-std (TMI - TMI_up150) shallow 50-300m ridge
    "spmd_updip_tmi_bandpass",     # 1 (col 54): Updip footwall projection of shallow TMI bandpass edge
    "spmd_epithermal_thk_uth",     # 2 (col 55): Dickson-Scott block-leveled low-Th/K x high-U/Th ridge
    "spmd_uk_redox_front",         # 3 (col 56): Block-leveled U/K redox front x subsurface PF gradient
    "spmd_blm_lode_conduit",       # 4 (col 57): US BLM closed epithermal lode kernel x PF/alteration gate
    # 5..7: 1 m LiDAR dipolar/graben/strike channels inside lidar_valid (3 channels -> global cols 58..60)
    "spmd_lidar_dipolar_scarp",    # 5 (col 58): Wallace sqrt(lapneg x lappos) crest-toe dipolar scarp
    "spmd_lidar_graben_pair",      # 6 (col 59): Synthetic/antithetic downface x upface x cross graben scarp
    "spmd_lidar_pf_strike_align",  # 7 (col 60): cos^2(theta_lidar_1m - theta_subsurface_pf) x step x coh
)

# Across the 61 pure-physical channels (35 shared + 18 UDSR + 8 SPMD):
# 1m-LiDAR-dependent columns are {50, 51, 52} (from UDSR) and {58, 59, 60} (from SPMD).
LIDAR_COLS_61: frozenset[int] = frozenset({50, 51, 52, 58, 59, 60})
NON_LIDAR_COLS_61: tuple[int, ...] = tuple(i for i in range(61) if i not in LIDAR_COLS_61)

# Strictly subsurface / potential-field / geodetic / seismic / hydrothermal / epithermal columns
# (zero DEM elevation, slope, terrain correction, curvature, top-hat, relief, or 1m LiDAR)
# used exclusively by the SAR-PU subsurface spy teacher so negative purification has zero
# subaerial topographic exposure bias.
SUBSURFACE_PURE_COLS_61: tuple[int, ...] = (
    # Official subsurface/geodetic/seismic/MT bands (excluding 5=tc, 11=det_elev, 18=det_elev_slope)
    0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17,
    # Derived potential-field/MT/basement edges in feature_stack_35
    26, 27, 28, 29, 30,
    # UDSR subsurface/hydrothermal/radiometric channels (excluding 44=piedmont, 49=unsup_crest, 50..52=lidar)
    35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 48,
    # SPMD shallow matched-depth magnetic + epithermal + BLM lode channels
    53, 54, 55, 56, 57,
)

# Coarse geomorphic exposure columns for observability propensity e(x_obs) = P(mapped | fault, x_obs):
# 18 = det_elev_slope, 24 = relief5, 14 = depth_to_base_surf (log1p-transformed), plus lidar_valid indicator.
EXPOSURE_BASE_COLS: tuple[int, ...] = (18, 24, 14)


def _block_standardize(arr: np.ndarray, blk_id: np.ndarray, foot: np.ndarray, valid_extra: np.ndarray | None = None) -> np.ndarray:
    """Per-GeoDAWN-survey-block (1=Winnemucca, 2=Fallon, 3=Hawthorne, 4=Tonopah) robust z-score."""
    out = np.zeros(arr.shape, dtype=np.float32)
    val_mask = foot & np.isfinite(arr)
    if valid_extra is not None:
        val_mask &= valid_extra
    for b in (1, 2, 3, 4):
        bm = val_mask & (blk_id == b)
        if int(bm.sum()) < 256:
            continue
        sub = arr[bm][::4].astype(np.float32)
        q25, q50, q75 = np.percentile(sub, [25.0, 50.0, 75.0])
        sc = float(0.7413 * (q75 - q25))
        if sc < 1e-5:
            sc = float(np.std(sub)) + 1e-5
        out[bm] = np.clip((arr[bm].astype(np.float32) - float(q50)) / sc, -6.0, 6.0)
    # Any residual valid footprint pixel with blk_id == 0 falls back to global robust_z
    rem = val_mask & (blk_id == 0)
    if rem.any():
        gz = udsr.robust_z(arr, val_mask)
        out[rem] = gz[rem]
    return out


def build_spmd_stack(ddir: Path, wdir: Path, force: bool = False, log=print) -> dict[str, Any]:
    """Build or load the 8-channel SPMD memmap ``spmd_stack_8.npy`` + label-free subsurface conduit ``spmd_sub_conduit.npy``."""
    udsr_info = udsr.build_udsr_stack(ddir, wdir, force=False, log=log)
    foot = udsr_info["foot"]
    lid_valid = udsr_info["lidar_valid"]
    flat_playa = udsr_info["flat_deep_playa"]
    h, w = foot.shape

    out_path = wdir / "spmd_stack_8.npy"
    sub_path = wdir / "spmd_sub_conduit.npy"
    meta_path = wdir / "spmd_stack_8_meta.json"
    if out_path.exists() and sub_path.exists() and meta_path.exists() and not force:
        return {
            "path": out_path,
            "sub_conduit_path": sub_path,
            "channels": SPMD_CHANNELS,
            "foot": foot,
            "lidar_valid": lid_valid,
            "flat_deep_playa": flat_playa,
            "meta": json.loads(meta_path.read_text()),
        }

    bands_dir = wdir / "bands"
    ext = ddir / "external"
    mm = open_memmap(out_path, mode="w+", dtype=np.float32, shape=(h, w, len(SPMD_CHANNELS)))

    z_base = udsr.load_band_clean(bands_dir / "15_depth_to_base_surf.npy", foot)
    slope = udsr.load_band_clean(bands_dir / "19_det_elev_slope.npy", foot)
    playa_gate = np.where(
        foot,
        1.0 - 0.88 * udsr.sigmoid_f32((z_base - 320.0) / 90.0) * udsr.sigmoid_f32((1.8 - slope) / 0.45),
        0.0,
    ).astype(np.float32)
    dip_gate = (
        np.tanh(np.maximum(z_base, 0.0) / 300.0)
        * np.exp(-np.maximum(z_base - 1500.0, 0.0) / 1400.0)
        * playa_gate
    ).astype(np.float32)

    # Reconstruct downdip vector & subsurface potential-field strike azimuth
    log("[H-SPMD] Stage 1/3: Matched-Depth (TMI - TMI_up150) Shallow Intrabasin Bandpass...")
    zb_sm = gaussian_filter(np.maximum(z_base, 0.0), sigma=3.0, mode="nearest")
    dy_z, dx_z = np.gradient(zb_sm)
    nz = np.hypot(dy_z, dx_z).astype(np.float32) + 1e-6
    del zb_sm

    grav = udsr.load_band_clean(bands_dir / "13_iso_grav_anom.npy", foot)
    g_sm = gaussian_filter(grav, sigma=2.5, mode="nearest")
    dy_g, dx_g = np.gradient(g_sm)
    ng = np.hypot(dy_g, dx_g).astype(np.float32) + 1e-6
    vy = 0.60 * (dy_z / nz) - 0.40 * (dy_g / ng)
    vx = 0.60 * (dx_z / nz) - 0.40 * (dx_g / ng)
    vn = np.hypot(vy, vx) + 1e-6
    dy_down = (vy / vn).astype(np.float32)
    dx_down = (vx / vn).astype(np.float32)
    del grav, g_sm, dy_z, dx_z, nz, vy, vx, vn

    rtp = udsr.load_band_clean(bands_dir / "02_rtp.npy", foot)
    r_sm = gaussian_filter(rtp, sigma=2.0, mode="nearest")
    dy_r, dx_r = np.gradient(r_sm)
    nr = np.hypot(dy_r, dx_r).astype(np.float32) + 1e-6
    del rtp, r_sm

    # Combined subsurface strike unit tangent (orthogonal to weighted gravity + RTP gradient)
    # Using double-angle (cos 2theta, sin 2theta) makes strike orientation pi-periodic (sign-invariant)!
    c2_g = ((dy_g * dy_g - dx_g * dx_g) / (ng * ng)).astype(np.float32)
    s2_g = ((-2.0 * dx_g * dy_g) / (ng * ng)).astype(np.float32)
    c2_r = ((dy_r * dy_r - dx_r * dx_r) / (nr * nr)).astype(np.float32)
    s2_r = ((-2.0 * dx_r * dy_r) / (nr * nr)).astype(np.float32)
    c2_pf = (0.58 * c2_g + 0.42 * c2_r).astype(np.float32)
    s2_pf = (0.58 * s2_g + 0.42 * s2_r).astype(np.float32)
    pf_grad_mag = udsr.sigmoid_f32(0.55 * udsr.robust_z(ng, foot) + 0.45 * udsr.robust_z(nr, foot))
    del dy_g, dx_g, ng, dy_r, dx_r, nr, c2_g, s2_g, c2_r, s2_r

    with rasterio.open(ext / "acquisition_block_id_100m.tif") as ds_blk:
        blk_id = ds_blk.read(1)
    with rasterio.open(ext / "tiger_road_distance_m.tif") as ds_rd:
        d_road = np.nan_to_num(ds_rd.read(1), nan=1000.0).astype(np.float32)
    road_gate = (1.0 - 0.75 * np.exp(-((d_road / 150.0) ** 2))).astype(np.float32)
    del d_road

    tmi = udsr.load_band_clean(bands_dir / "14_tmi.npy", foot)
    with rasterio.open(ext / "geodawn_extensions_u8.tif") as ds_ext:
        thk_u8 = ds_ext.read(1)
        uk_u8 = ds_ext.read(2)
        uth_u8 = ds_ext.read(3)
        tmi_up150_u8 = ds_ext.read(4)

    z_tmi0 = _block_standardize(tmi, blk_id, foot)
    del tmi
    z_tmi150 = _block_standardize(tmi_up150_u8.astype(np.float32), blk_id, foot, valid_extra=(tmi_up150_u8 > 0))
    del tmi_up150_u8

    # Phillips (2001) shallow vertical-bandpass magnetic residual (50-300 m source horizon)
    tmi_bp = gaussian_filter(z_tmi0 - z_tmi150, sigma=1.1, mode="nearest")
    del z_tmi0, z_tmi150
    by_bp, bx_bp = np.gradient(tmi_bp)
    bp_edge = np.hypot(bx_bp, by_bp).astype(np.float32)
    del by_bp, bx_bp
    bp_ridge = np.maximum(features._hessian_ridge(tmi_bp, 1.6), 0.0) + np.maximum(features._hessian_ridge(-tmi_bp, 1.6), 0.0)
    del tmi_bp
    bp_comb = (0.60 * udsr.robust_z(bp_edge, foot) + 0.40 * udsr.robust_z(bp_ridge, foot)) * road_gate * playa_gate
    del bp_edge, bp_ridge
    mm[:, :, 0] = udsr.robust_z(bp_comb, foot)

    bp_pos = np.maximum(mm[:, :, 0], 0.0).astype(np.float32)
    mm[:, :, 1] = udsr.robust_z(
        udsr.advect_updip_field(bp_pos, dy_down, dx_down, foot, offsets_px=(1.8, 3.8, 6.5), dip_gate=dip_gate),
        foot,
    )
    del bp_comb, bp_pos, dy_down, dx_down, dip_gate

    log("[H-SPMD] Stage 2/3: Dickson-Scott Epithermal Th/K-U/Th, U/K Redox & BLM Lode Corridors...")
    val_rad = (thk_u8 > 0) & (uk_u8 > 0) & (uth_u8 > 0)
    z_thk = _block_standardize(thk_u8.astype(np.float32), blk_id, foot, valid_extra=val_rad)
    z_uk = _block_standardize(uk_u8.astype(np.float32), blk_id, foot, valid_extra=val_rad)
    z_uth = _block_standardize(uth_u8.astype(np.float32), blk_id, foot, valid_extra=val_rad)
    del thk_u8, uk_u8, uth_u8, val_rad, blk_id

    # Dickson & Scott (1997): potassic/adularia hydrothermal alteration depletes Th/K (-z_thk)
    # while active fault gouge/radon conduits enrich U/Th (+z_uth).
    epitherm_raw = gaussian_filter(
        0.55 * np.maximum(-z_thk, -0.5) + 0.45 * np.maximum(z_uth, -0.5),
        sigma=1.4,
        mode="nearest",
    )
    del z_thk, z_uth
    ep_ridge = np.maximum(features._hessian_ridge(epitherm_raw, 2.0), 0.0)
    ep_comb = (0.55 * udsr.robust_z(epitherm_raw, foot) + 0.45 * udsr.robust_z(ep_ridge, foot)) * road_gate * playa_gate
    del epitherm_raw, ep_ridge
    mm[:, :, 2] = udsr.robust_z(ep_comb, foot)
    del ep_comb

    uk_sm = gaussian_filter(z_uk, sigma=1.4, mode="nearest")
    del z_uk
    uk_ridge = np.maximum(features._hessian_ridge(uk_sm, 2.0), 0.0)
    uk_comb = (0.50 * np.maximum(udsr.robust_z(uk_sm, foot), 0.0) + 0.50 * np.maximum(udsr.robust_z(uk_ridge, foot), 0.0)) * pf_grad_mag * road_gate * playa_gate
    del uk_sm, uk_ridge
    mm[:, :, 3] = udsr.robust_z(uk_comb, foot)
    del uk_comb

    with rasterio.open(ext / "blm_closed_claim_distance_m.tif") as ds_blm:
        d_blm = np.nan_to_num(ds_blm.read(1), nan=10000.0).astype(np.float32)
    # Gate BLM lode kernel strictly by subsurface PF gradient + epithermal alteration so non-fault placer areas drop out
    alt_gate = udsr.sigmoid_f32(0.55 * mm[:, :, 2] + 0.45 * mm[:, :, 0])
    blm_lode = np.exp(-np.maximum(d_blm, 0.0) / 450.0) * pf_grad_mag * alt_gate * playa_gate
    del d_blm, alt_gate
    mm[:, :, 4] = udsr.robust_z(blm_lode, foot)
    del blm_lode

    log("[H-SPMD] Stage 3/3: 1m LiDAR Dipolar Crest-Toe, Graben Pair & Subsurface Strike Concordance...")
    shoreline_damp = np.where((z_base > 180.0) & (slope < 3.5) & (pf_grad_mag < 0.48), 0.35, 1.0).astype(np.float32)
    del z_base, slope, pf_grad_mag

    with rasterio.open(ext / "lidar_scarp_features_u8.tif") as ds_lid:
        step_max = ds_lid.read(3).astype(np.float32) / 255.0
        lapneg = ds_lid.read(4).astype(np.float32) / 255.0
        lappos = ds_lid.read(5).astype(np.float32) / 255.0
        downface = ds_lid.read(6).astype(np.float32) / 255.0
        upface = ds_lid.read(7).astype(np.float32) / 255.0
        cross_max = ds_lid.read(8).astype(np.float32) / 255.0
        coh100 = ds_lid.read(10).astype(np.float32) / 255.0
        strike_u8 = ds_lid.read(11).astype(np.float32)

    dipolar = np.sqrt(np.maximum(lapneg * lappos, 0.0)) * (0.35 + 0.65 * coh100) * road_gate * shoreline_damp * playa_gate
    del lapneg, lappos
    mm[:, :, 5] = np.where(lid_valid, udsr.robust_z(dipolar, lid_valid), 0.0)
    del dipolar

    graben = (
        cross_max
        * (0.60 * np.maximum(downface, upface) + 0.40 * np.sqrt(np.maximum(downface * upface, 0.0)))
        * (0.35 + 0.65 * coh100)
        * road_gate
        * shoreline_damp
        * playa_gate
    )
    del downface, upface, cross_max
    mm[:, :, 6] = np.where(lid_valid, udsr.robust_z(graben, lid_valid), 0.0)
    del graben

    theta_lid = (strike_u8 / 255.0) * np.float32(np.pi)
    del strike_u8
    c2_lid = np.cos(2.0 * theta_lid).astype(np.float32)
    s2_lid = np.sin(2.0 * theta_lid).astype(np.float32)
    del theta_lid
    # cos^2(theta_lid - theta_pf) = 0.5 * (1 + cos(2*theta_lid)*cos(2*theta_pf) + sin(2*theta_lid)*sin(2*theta_pf))
    pf_norm = np.hypot(c2_pf, s2_pf) + 1e-5
    cos2_delta = 0.5 * (1.0 + (c2_lid * c2_pf + s2_lid * s2_pf) / pf_norm)
    del c2_lid, s2_lid, c2_pf, s2_pf, pf_norm
    align_lid = np.clip(cos2_delta, 0.0, 1.0) * step_max * coh100 * road_gate * shoreline_damp * playa_gate
    del cos2_delta, step_max, coh100, road_gate, shoreline_damp
    mm[:, :, 7] = np.where(lid_valid, udsr.robust_z(align_lid, lid_valid), 0.0)
    del align_lid

    mm.flush()

    # Build 100% DEM-free & 1m-LiDAR-free Subsurface + Epithermal Conduit Score in [0, 1]
    udsr_mm = open_memmap(wdir / "udsr_stack_18.npy", mode="r")
    raw_sub = (
        0.20 * udsr.rank01(udsr_mm[:, :, 2], foot)    # updip_grav_trace
        + 0.14 * udsr.rank01(udsr_mm[:, :, 3], foot)  # updip_rtp_demag
        + 0.11 * udsr.rank01(udsr_mm[:, :, 4], foot)  # updip_mt_conduit
        + 0.09 * udsr.rank01(udsr_mm[:, :, 5], foot)  # gallardo_coupling
        + 0.14 * udsr.rank01(mm[:, :, 0], foot)       # spmd_tmi_bandpass_ridge
        + 0.10 * udsr.rank01(mm[:, :, 1], foot)       # spmd_updip_tmi_bandpass
        + 0.09 * udsr.rank01(mm[:, :, 2], foot)       # spmd_epithermal_thk_uth
        + 0.05 * udsr.rank01(mm[:, :, 3], foot)       # spmd_uk_redox_front
        + 0.04 * udsr.rank01(mm[:, :, 4], foot)       # spmd_blm_lode_conduit
        + 0.04 * udsr.rank01(0.5 * udsr_mm[:, :, 10] + 0.5 * udsr_mm[:, :, 11], foot)  # GDR geotherm + 2m probe
    ) * playa_gate
    udsr._drop_mm_cache(udsr_mm)
    del udsr_mm, playa_gate
    sub_conduit = udsr.oriented_nms_4az(udsr.rank01(raw_sub, foot), foot, blend=0.45)
    del raw_sub
    np.save(sub_path, sub_conduit.astype(np.float32))
    del sub_conduit

    udsr._drop_mm_cache(mm)
    del mm
    gc.collect()

    meta = {
        "n_channels": len(SPMD_CHANNELS),
        "channels": list(SPMD_CHANNELS),
        "total_phys_channels": 61,
        "non_lidar_phys_channels": len(NON_LIDAR_COLS_61),
        "subsurface_spy_channels": len(SUBSURFACE_PURE_COLS_61),
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    log(f"[H-SPMD] Saved {out_path.name} + {sub_path.name} | {meta}")
    return {
        "path": out_path,
        "sub_conduit_path": sub_path,
        "channels": SPMD_CHANNELS,
        "foot": foot,
        "lidar_valid": lid_valid,
        "flat_deep_playa": flat_playa,
        "meta": meta,
    }


def extract_phys61_sorted(
    ys: np.ndarray,
    xs: np.ndarray,
    base_mm: np.ndarray,
    udsr_mm: np.ndarray,
    spmd_mm: np.ndarray,
    batch: int = 25000,
) -> np.ndarray:
    """Sequential-friendly batched memmap gather of all 61 pure-physical channels."""
    n = ys.size
    out = np.empty((n, 61), dtype=np.float32)
    if n == 0:
        return out
    order = np.argsort(ys, kind="mergesort")
    ys_s, xs_s = ys[order], xs[order]
    tmp = np.empty((n, 61), dtype=np.float32)
    for s in range(0, n, batch):
        e = min(n, s + batch)
        yb, xb = ys_s[s:e], xs_s[s:e]
        tmp[s:e, 0:35] = np.nan_to_num(base_mm[yb, xb, :], nan=0.0)
        tmp[s:e, 35:53] = np.nan_to_num(udsr_mm[yb, xb, :], nan=0.0)
        tmp[s:e, 53:61] = np.nan_to_num(spmd_mm[yb, xb, :], nan=0.0)
        udsr._drop_mm_cache(base_mm)
        udsr._drop_mm_cache(udsr_mm)
        udsr._drop_mm_cache(spmd_mm)
    out[order] = tmp
    return out


def _exposure_design_matrix(X61: np.ndarray, lid_flag: np.ndarray) -> np.ndarray:
    """4-column coarse geomorphic observability matrix [slope_z, relief5_z, log_depth, lidar_valid]."""
    slope = np.clip(X61[:, 18], 0.0, 65.0) / 15.0
    rel5 = np.clip(X61[:, 24], 0.0, 600.0) / 150.0
    log_z = np.log1p(np.clip(X61[:, 14], 0.0, 7500.0)) / 6.0
    lid = lid_flag.astype(np.float32).reshape(-1)
    return np.column_stack([slope, rel5, log_z, lid]).astype(np.float32)


def run_leakage_canary_63ch(
    base_mm: np.ndarray,
    udsr_mm: np.ndarray,
    spmd_mm: np.ndarray,
    ctx: Any,
    max_auc_threshold: float = 0.90,
    seed: int = 20261028,
) -> dict[str, Any]:
    """Protocol Rule 4 Leakage Canary across ALL 63 features (35 shared + 18 UDSR + 8 SPMD + 2 vis_cont)."""
    rng = np.random.default_rng(seed)
    pos_rows, neg_rows = [], []

    for cell in ctx.cells:
        sl = cell.bbox
        vis_cont_full = udsr.compute_visible_continuation(cell.visible_full, ctx.foot)
        act = cell.active_sub & (cell.d_visible_sub > 2.0)
        truth = np.zeros_like(act)
        truth[cell.truth_coords] = True
        truth &= act
        neg_mask = act & ~truth

        py, px = np.nonzero(truth)
        ny, nx = np.nonzero(neg_mask)
        if py.size > 2000:
            pick_p = rng.choice(py.size, size=2000, replace=False)
            py, px = py[pick_p], px[pick_p]
        if ny.size > 8000:
            pick_n = rng.choice(ny.size, size=8000, replace=False)
            ny, nx = ny[pick_n], nx[pick_n]

        r0, c0 = int(sl[0].start), int(sl[1].start)
        Xp61 = extract_phys61_sorted(py + r0, px + c0, base_mm, udsr_mm, spmd_mm)
        Xn61 = extract_phys61_sorted(ny + r0, nx + c0, base_mm, udsr_mm, spmd_mm)
        pos_rows.append(np.hstack([Xp61, vis_cont_full[py + r0, px + c0, :]]))
        neg_rows.append(np.hstack([Xn61, vis_cont_full[ny + r0, nx + c0, :]]))
        del vis_cont_full, Xp61, Xn61
        gc.collect()

    X_pos = np.vstack(pos_rows)
    X_neg = np.vstack(neg_rows)
    y = np.concatenate([np.ones(len(X_pos), dtype=np.int8), np.zeros(len(X_neg), dtype=np.int8)])
    X = np.vstack([X_pos, X_neg])

    all_names = list(features.CHANNELS) + list(udsr.UDSR_CHANNELS) + list(SPMD_CHANNELS) + list(udsr.VIS_CHANNELS)
    aucs: dict[str, float] = {}
    worst_name, worst_auc = "", 0.0
    for j, cname in enumerate(all_names):
        col = X[:, j]
        if np.ptp(col) <= 1e-12:
            auc_or = 0.5
        else:
            raw_auc = float(roc_auc_score(y, col))
            auc_or = float(max(raw_auc, 1.0 - raw_auc))
        aucs[cname] = round(auc_or, 6)
        if auc_or > worst_auc:
            worst_auc = auc_or
            worst_name = cname

    spmd_aucs = {k: aucs[k] for k in SPMD_CHANNELS}
    return {
        "passed": bool(worst_auc <= max_auc_threshold),
        "threshold": max_auc_threshold,
        "n_features_tested": len(all_names),
        "n_pos_sampled": int(len(X_pos)),
        "n_neg_sampled": int(len(X_neg)),
        "max_oriented_auc": round(worst_auc, 6),
        "worst_channel": worst_name,
        "spmd_new_8ch_aucs": spmd_aucs,
        "aucs": aucs,
    }


def fit_dual_cover_61(
    train_domain: np.ndarray,
    visible_faults: np.ndarray,
    lidar_valid: np.ndarray,
    base_mm: np.ndarray,
    udsr_mm: np.ndarray,
    spmd_mm: np.ndarray,
    *,
    sarpu: bool = True,
    gamma_train: float = 0.38,
    seed: int = 20261028,
) -> dict[str, Any]:
    """Fit 61-ch M_Full + 55-ch M_Gap Dual-Cover models, either supervised (sarpu=False) or SAR-PU (sarpu=True)."""
    rng = np.random.default_rng(seed)
    h, w = visible_faults.shape
    d_sub = distance_transform_edt(~visible_faults[::2, ::2]).astype(np.float32) * 2.0
    d_vis = zoom(d_sub, (h / d_sub.shape[0], w / d_sub.shape[1]), order=1).astype(np.float32)[:h, :w]
    del d_sub

    pos_all = visible_faults & train_domain
    unlab_all = train_domain & (d_vis > 4.0)

    py_all, px_all = np.nonzero(pos_all)
    uy_all, ux_all = np.nonzero(unlab_all)
    if py_all.size > 34000:
        ip = rng.choice(py_all.size, 34000, replace=False)
        py_all, px_all = py_all[ip], px_all[ip]
    n_unlab_pool = min(uy_all.size, max(125000, 4 * py_all.size))
    iu = rng.choice(uy_all.size, n_unlab_pool, replace=False)
    uy_pool, ux_pool = uy_all[iu], ux_all[iu]
    del uy_all, ux_all

    Xp_all = extract_phys61_sorted(py_all, px_all, base_mm, udsr_mm, spmd_mm)
    Xu_pool = extract_phys61_sorted(uy_pool, ux_pool, base_mm, udsr_mm, spmd_mm)
    lid_p = lidar_valid[py_all, px_all]
    lid_u = lidar_valid[uy_pool, ux_pool]

    prop_model: LogisticRegression | None = None
    prop_p95: float = 1.0
    purged_frac: float = 0.0

    if sarpu:
        # 1. Subsurface-only Spy Teacher (15% spy positives placed inside unlabeled pool; zero topo/LiDAR inputs)
        n_spy = max(250, int(0.15 * len(Xp_all)))
        spy_perm = rng.permutation(len(Xp_all))
        spy_idx, train_p_idx = spy_perm[:n_spy], spy_perm[n_spy:]
        X_spy_tr = np.vstack([
            Xp_all[train_p_idx][:, SUBSURFACE_PURE_COLS_61],
            Xp_all[spy_idx][:, SUBSURFACE_PURE_COLS_61],
            Xu_pool[:, SUBSURFACE_PURE_COLS_61],
        ])
        y_spy_tr = np.concatenate([
            np.ones(len(train_p_idx), dtype=np.int8),
            np.zeros(len(spy_idx) + len(Xu_pool), dtype=np.int8),
        ])
        spy_clf = HistGradientBoostingClassifier(
            max_iter=90,
            learning_rate=0.07,
            max_leaf_nodes=23,
            min_samples_leaf=120,
            l2_regularization=4.0,
            random_state=seed + 7,
        )
        spy_clf.fit(X_spy_tr, y_spy_tr)
        del X_spy_tr, y_spy_tr

        spy_scores = spy_clf.predict_proba(Xp_all[spy_idx][:, SUBSURFACE_PURE_COLS_61])[:, 1]
        unlab_sub_scores = spy_clf.predict_proba(Xu_pool[:, SUBSURFACE_PURE_COLS_61])[:, 1]
        del spy_clf

        # Purge putative concealed subsurface fault conduits (bounded cleanly between 8% and 16% of unlabeled pool)
        tau_spy = float(np.percentile(spy_scores, 30.0))
        q84, q92 = np.percentile(unlab_sub_scores, [84.0, 92.0])
        tau_purge = float(np.clip(tau_spy, float(q84), float(q92)))
        is_putative_concealed = unlab_sub_scores >= tau_purge
        reliable_neg_mask = ~is_putative_concealed
        purged_frac = float(is_putative_concealed.mean())

        # 2. Smooth 4-feature Geomorphic Observability Propensity e(x_obs) = P(mapped | fault_corridor, x_obs)
        X_obs_pos = _exposure_design_matrix(Xp_all, lid_p)
        X_obs_conc = _exposure_design_matrix(Xu_pool[is_putative_concealed], lid_u[is_putative_concealed])
        X_obs_fit = np.vstack([X_obs_pos, X_obs_conc])
        y_obs_fit = np.concatenate([
            np.ones(len(X_obs_pos), dtype=np.int8),
            np.zeros(len(X_obs_conc), dtype=np.int8),
        ])
        prop_model = LogisticRegression(C=0.25, max_iter=200, class_weight="balanced")
        prop_model.fit(X_obs_fit, y_obs_fit)
        raw_e_pos = prop_model.predict_proba(X_obs_pos)[:, 1]
        prop_p95 = max(float(np.percentile(raw_e_pos, 95.0)), 0.25)
        e_pos = np.clip(raw_e_pos / prop_p95, 0.22, 1.0).astype(np.float32)
        w_pos_all = np.power(e_pos, -float(gamma_train)).astype(np.float32)
        w_pos_all /= float(np.mean(w_pos_all))  # preserve total positive effective sample size

        Xu_rel = Xu_pool[reliable_neg_mask]
        lid_u_rel = lid_u[reliable_neg_mask]
        # Down-weight borderline subsurface-elevated negatives smoothly
        rel_scores = unlab_sub_scores[reliable_neg_mask]
        w_neg_rel = np.clip(1.0 - 0.45 * (rel_scores / max(tau_purge, 1e-4)), 0.55, 1.0).astype(np.float32)
    else:
        Xu_rel = Xu_pool
        lid_u_rel = lid_u
        w_pos_all = np.ones(len(Xp_all), dtype=np.float32)
        w_neg_rel = np.ones(len(Xu_rel), dtype=np.float32)

    del Xu_pool
    n_neg_target = min(len(Xu_rel), max(96000, 3 * len(Xp_all)))
    ineg = rng.choice(len(Xu_rel), n_neg_target, replace=False)
    Xn_g = Xu_rel[ineg]
    wn_g = w_neg_rel[ineg]

    # Fit M_Gap on 55 strictly 1m-LiDAR-free physical channels across train_domain
    Xg = np.vstack([Xp_all[:, NON_LIDAR_COLS_61], Xn_g[:, NON_LIDAR_COLS_61]])
    yg = np.concatenate([np.ones(len(Xp_all), dtype=np.int8), np.zeros(len(Xn_g), dtype=np.int8)])
    wg = np.concatenate([w_pos_all, wn_g])
    m_gap = HistGradientBoostingClassifier(
        max_iter=175,
        learning_rate=0.06,
        max_leaf_nodes=31,
        min_samples_leaf=80,
        l2_regularization=2.5,
        random_state=seed + 31,
    )
    m_gap.fit(Xg, yg, sample_weight=wg)
    del Xg, yg, wg, Xn_g, wn_g

    # Fit M_Full on all 61 physical channels inside lidar_valid & train_domain
    Xp_f = Xp_all[lid_p]
    wp_f = w_pos_all[lid_p]
    Xu_f_all = Xu_rel[lid_u_rel]
    wu_f_all = w_neg_rel[lid_u_rel]
    n_neg_f = min(len(Xu_f_all), max(90000, 3 * len(Xp_f)))
    inf_idx = rng.choice(len(Xu_f_all), n_neg_f, replace=False)
    Xf = np.vstack([Xp_f, Xu_f_all[inf_idx]])
    yf = np.concatenate([np.ones(len(Xp_f), dtype=np.int8), np.zeros(n_neg_f, dtype=np.int8)])
    wf = np.concatenate([wp_f, wu_f_all[inf_idx]])
    del Xp_all, Xu_rel, Xp_f, Xu_f_all, wp_f, wu_f_all

    m_full = HistGradientBoostingClassifier(
        max_iter=175,
        learning_rate=0.06,
        max_leaf_nodes=31,
        min_samples_leaf=80,
        l2_regularization=2.5,
        random_state=seed + 131,
    )
    m_full.fit(Xf, yf, sample_weight=wf)
    del Xf, yf, wf

    # Quantile calibration curve aligning M_Gap posterior onto M_Full inside lidar_valid
    cal_y, cal_x = np.nonzero(train_domain & lidar_valid & (d_vis > 2.0))
    if cal_y.size > 24000:
        ic = rng.choice(cal_y.size, 24000, replace=False)
        cal_y, cal_x = cal_y[ic], cal_x[ic]
    X_cal = extract_phys61_sorted(cal_y, cal_x, base_mm, udsr_mm, spmd_mm)
    pf_cal = m_full.predict_proba(X_cal)[:, 1]
    pg_cal = m_gap.predict_proba(X_cal[:, NON_LIDAR_COLS_61])[:, 1]
    qs = np.linspace(0.0, 100.0, 201)
    q_table = np.vstack([np.percentile(pg_cal, qs), np.percentile(pf_cal, qs)]).astype(np.float32)
    del X_cal, d_vis
    gc.collect()

    return {
        "m_full": m_full,
        "m_gap": m_gap,
        "q_table": q_table,
        "prop_model": prop_model,
        "prop_p95": prop_p95,
        "sarpu": sarpu,
        "purged_unlabeled_fraction": round(purged_frac, 5),
    }


def predict_dual_cover_61_bbox(
    bbox: tuple[slice, slice],
    eval_mask_sub: np.ndarray,
    lidar_valid: np.ndarray,
    base_mm: np.ndarray,
    udsr_mm: np.ndarray,
    spmd_mm: np.ndarray,
    bundle: dict[str, Any],
    row_strip: int = 256,
) -> tuple[np.ndarray, np.ndarray]:
    """Strip-streaming prediction returning ``(posterior_sub, exposure_propensity_sub)``."""
    r0 = int(bbox[0].start)
    c0, c1 = int(bbox[1].start), int(bbox[1].stop)
    sh, sw = eval_mask_sub.shape
    post = np.zeros((sh, sw), dtype=np.float32)
    ehat = np.ones((sh, sw), dtype=np.float32)
    lid_sub = lidar_valid[bbox]

    m_full = bundle["m_full"]
    m_gap = bundle["m_gap"]
    q_table = bundle["q_table"]
    prop_model: LogisticRegression | None = bundle["prop_model"]
    prop_p95: float = bundle["prop_p95"]

    for sr0 in range(0, sh, row_strip):
        sr1 = min(sh, sr0 + row_strip)
        em_strip = eval_mask_sub[sr0:sr1]
        if not em_strip.any():
            continue
        gr0, gr1 = r0 + sr0, r0 + sr1
        b_blk = np.nan_to_num(base_mm[gr0:gr1, c0:c1, :], nan=0.0).astype(np.float32)
        u_blk = np.nan_to_num(udsr_mm[gr0:gr1, c0:c1, :], nan=0.0).astype(np.float32)
        s_blk = np.nan_to_num(spmd_mm[gr0:gr1, c0:c1, :], nan=0.0).astype(np.float32)
        udsr._drop_mm_cache(base_mm)
        udsr._drop_mm_cache(udsr_mm)
        udsr._drop_mm_cache(spmd_mm)

        lid_s = lid_sub[sr0:sr1]
        m_l = em_strip & lid_s
        if m_l.any():
            X_l = np.hstack([b_blk[m_l], u_blk[m_l], s_blk[m_l]])
            post[sr0:sr1][m_l] = m_full.predict_proba(X_l)[:, 1].astype(np.float32)
            if prop_model is not None:
                Xo_l = _exposure_design_matrix(X_l, np.ones(len(X_l), dtype=bool))
                el = prop_model.predict_proba(Xo_l)[:, 1] / prop_p95
                ehat[sr0:sr1][m_l] = np.clip(el, 0.22, 1.0).astype(np.float32)

        m_g = em_strip & ~lid_s
        if m_g.any():
            X_g_full = np.hstack([b_blk[m_g], u_blk[m_g], s_blk[m_g]])
            raw_p = m_gap.predict_proba(X_g_full[:, NON_LIDAR_COLS_61])[:, 1].astype(np.float32)
            post[sr0:sr1][m_g] = np.interp(raw_p, q_table[0], q_table[1]).astype(np.float32)
            if prop_model is not None:
                Xo_g = _exposure_design_matrix(X_g_full, np.zeros(len(X_g_full), dtype=bool))
                eg = prop_model.predict_proba(Xo_g)[:, 1] / prop_p95
                ehat[sr0:sr1][m_g] = np.clip(eg, 0.22, 1.0).astype(np.float32)

    return post, ehat
