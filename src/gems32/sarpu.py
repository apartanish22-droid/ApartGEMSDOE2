"""H-SARPU: Selected-At-Random Propensity-Decontaminated PU & Blind Hydrothermal-LEFM Inversion.

Pre-registered lane documented in ``knowledge/preregistration_sarpu_20261028.md``:
  1. 12 new label-free blind-geothermal, spectral Baranov pseudo-gravity, GeoDAWN extension
     (Th/K, U/K, U/Th, shallow TMI - TMI_up150), BLM hydrothermal claim conduit, anisotropic
     strike-guided Darcy plume, real-band multi-scale Hurst/fractal anisotropy, and 1 m LiDAR
     Wallace (1977) scarp-dipole + LiDAR-to-potential-field strike concordance channels.
  2. 2 fold-local Linear Elastic Fracture Mechanics (LEFM) continuation channels (Williams 1957
     coplanar + horse-tail wing-crack tensile lobes; Crider & Pollard 1998 relay-ramp breaching)
     computed strictly from ``visible_mask`` with 5-group connected-component jackknifing on
     training folds so no training fault segment ever self-predicts.
  3. Selected-At-Random (SAR-PU) observation-propensity weighting + two-stage reliable-negative
     decontamination Dual-Cover ensemble (65 pure-physical channels inside 1 m LiDAR; 60 strictly
     1 m-LiDAR-free channels across the 24.66% LiDAR gap).

Engineered for strict < 1.1 GiB peak RSS on 2-vCPU, 3.8 GiB zero-swap containers.
"""
from __future__ import annotations

import gc
import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from numpy.lib.format import open_memmap
from scipy.ndimage import (
    distance_transform_edt,
    gaussian_filter,
    label,
    zoom,
)
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from . import features, udsr

SARPU_CHANNELS: tuple[str, ...] = (
    # 0..8 and 11: strictly 1 m LiDAR-free (10 channels)
    "sarpu_shallow_mag_demag",        # 0: 0-150m shallow vertical continuation magnetite loss (TMI vs TMI_up150)
    "sarpu_baranov_pseudograv_resid", # 1: Baranov (1957) FFT 1/|k| pseudo-gravity hydrothermal demag deficit
    "sarpu_geodawn_thk_adularia",     # 2: 4-block leveled GeoDAWN Th/K potassium-metasomatism trough ridge
    "sarpu_geodawn_radon_uk_uth",     # 3: 4-block leveled GeoDAWN U/K + U/Th 222Rn gas-conduit ridge
    "sarpu_blm_epithermal_conduit",   # 4: BLM hydrothermal/epithermal claim proximity x subsurface PF/MT root
    "sarpu_aniso_darcy_plume",        # 5: Strike-guided anisotropic Darcy/Screened-Poisson GDR #1391 plume
    "sarpu_biot_coulomb_potency",     # 6: Biot fluid-pressurized slip-dilation x log seismicity density
    "sarpu_lahontan_deconf_knick",    # 7: 100m DEM convex-concave profile-curvature scarp (shoreline-damped)
    "sarpu_fractal_roughness_aniso",  # 8: Real-band 200m/800m variogram Hurst roughness x strike anisotropy
    # 9..10: 1 m LiDAR-assisted inside lidar_valid >= 128 (2 channels)
    "sarpu_lidar_wallace_dipole",     # 9: Wallace (1977) convex-crest x concave-toe x downface LiDAR dipole
    "sarpu_lidar_strike_pf_concord",  # 10: 1m LiDAR scarp strike cos^2 concordance with deep PF strike
    # 11: strictly 1 m LiDAR-free AND DEM-slope-free subsurface blind-conduit composite [0, 1]
    "sarpu_blind_conduit_index",      # 11: Pure-subsurface hydrothermal/Baranov/updip blind conduit rank
)

LEFM_CHANNELS: tuple[str, ...] = (
    "vis_williams_mode1_2_lobe",      # 65: Williams (1957) coplanar + +/-35 deg wing-crack tensile lobes
    "vis_crider_pollard_relay",       # 66: Crider & Pollard (1998) en-echelon relay-ramp breaching stress
)

# Combined pure-physical feature space: 35 (base) + 18 (udsr) + 12 (sarpu) = 65 channels
# LiDAR-dependent indices in 65-channel space: udsr 15,16,17 (-> 50,51,52) and sarpu 9,10 (-> 62,63)
LIDAR_COLS_65: frozenset[int] = frozenset({50, 51, 52, 62, 63})
NON_LIDAR_COLS_65: tuple[int, ...] = tuple(i for i in range(65) if i not in LIDAR_COLS_65)

# Coupled LEFM + SARPU space: 65 + 2 = 67 channels
LIDAR_COLS_67: frozenset[int] = frozenset({50, 51, 52, 62, 63})
NON_LIDAR_COLS_67: tuple[int, ...] = tuple(i for i in range(67) if i not in LIDAR_COLS_67)

# Observation propensity covariates (exposure/scarp/cover visibility only):
# band19 det_elev_slope (18), relief5 (24), tophat2 (25), band15 depth_to_base_surf (14), udsr_piedmont (44)
PROPENSITY_COLS_65: tuple[int, ...] = (18, 24, 25, 14, 44)


def _baranov_pseudogravity_grad(rtp: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Compute horizontal gradient magnitude of Baranov (1957) radial-1/|k| pseudo-gravity on 2x grid.

    Pseudo-gravity integrates magnetic potential in wavenumber space (1/|k|), so >99.9% of spectral
    power resides at wavelengths >= 400 m (2x 100 m grid), keeping FFT peak RAM < 16 MB.
    """
    h, w = rtp.shape
    r_sub = udsr.robust_z(rtp, foot)[::2, ::2].astype(np.float32)
    sh, sw = r_sub.shape
    # Taper borders smoothly to suppress periodic wrap-around
    wy = np.hanning(sh).astype(np.float32)[:, None]
    wx = np.hanning(sw).astype(np.float32)[None, :]
    taper = np.sqrt(np.clip(wy * wx, 0.05, 1.0))
    spec = np.fft.rfft2(r_sub * taper)
    ky = np.fft.fftfreq(sh, d=0.2).astype(np.float32)[:, None]   # cycles / km (200 m grid)
    kx = np.fft.rfftfreq(sw, d=0.2).astype(np.float32)[None, :]
    kr = np.hypot(ky, kx)
    # Band-limited 1/|k| integration filter: taper long wavelengths (>35 km) and Nyquist (>2.0 cyc/km)
    hp = 1.0 - np.exp(-((kr / 0.035) ** 2))
    lp = np.exp(-((kr / 1.6) ** 4))
    inv_k = np.where(kr > 1e-5, (hp * lp) / np.maximum(kr, 1e-4), 0.0).astype(np.float32)
    pg_sub = np.fft.irfft2(spec * inv_k, s=(sh, sw)).astype(np.float32)
    gy, gx = np.gradient(pg_sub)
    grad_sub = np.hypot(gx, gy).astype(np.float32)
    out = zoom(grad_sub, (h / sh, w / sw), order=1).astype(np.float32)[:h, :w]
    out[~foot] = 0.0
    return out


def _anisotropic_strike_plume(
    src_full: np.ndarray,
    tx_full: np.ndarray,
    ty_full: np.ndarray,
    foot: np.ndarray,
    n_steps: int = 18,
    kappa_par: float = 0.22,
    kappa_perp: float = 0.04,
    decay: float = 0.035,
) -> np.ndarray:
    """Solve anisotropic Screened-Poisson / Darcy plume diffusion along local fault strike on 2x grid.

    Models hydrothermal fluid & heat dispersion 5.5x faster along permeable fault-damage strike
    tangent ``t = (tx, ty)`` than across low-permeability fault-core gouge (Caine et al., 1996).
    """
    h, w = src_full.shape
    s = np.maximum(src_full[::2, ::2], 0.0).astype(np.float32)
    tx = tx_full[::2, ::2].astype(np.float32)
    ty = ty_full[::2, ::2].astype(np.float32)
    f_sub = foot[::2, ::2]

    # Tensor components D = k_perp * I + (k_par - k_perp) * t t^T
    dk = np.float32(kappa_par - kappa_perp)
    dxx = (np.float32(kappa_perp) + dk * tx * tx).astype(np.float32)
    dyy = (np.float32(kappa_perp) + dk * ty * ty).astype(np.float32)
    dxy = (dk * tx * ty).astype(np.float32)

    u = s.copy()
    for _ in range(n_steps):
        p = np.pad(u, 1, mode="edge")
        uyy = p[2:, 1:-1] - 2.0 * u + p[:-2, 1:-1]
        uxx = p[1:-1, 2:] - 2.0 * u + p[1:-1, :-2]
        uxy = 0.25 * (p[2:, 2:] - p[2:, :-2] - p[:-2, 2:] + p[:-2, :-2])
        div_du = dxx * uxx + dyy * uyy + 2.0 * dxy * uxy
        u = np.maximum((1.0 - decay) * u + div_du + 0.12 * s, 0.0).astype(np.float32)
        u[~f_sub] = 0.0

    out = zoom(u, (h / u.shape[0], w / u.shape[1]), order=1).astype(np.float32)[:h, :w]
    out[~foot] = 0.0
    return out


def _block_standardize_u8(
    arr_u8: np.ndarray,
    blk_id: np.ndarray,
    foot: np.ndarray,
    invert: bool = False,
) -> np.ndarray:
    """Standardize uint8 GeoDAWN channel within each contractor flight block (1..4)."""
    out = np.zeros(arr_u8.shape, dtype=np.float32)
    af = arr_u8.astype(np.float32)
    for b in np.unique(blk_id[foot]):
        m = foot & (blk_id == b) & (arr_u8 > 0)
        if m.sum() < 200:
            continue
        vals = af[m]
        q25, q50, q75 = np.percentile(vals[::4], [25.0, 50.0, 75.0])
        sc = float(0.7413 * (q75 - q25)) + 1e-5
        z = (vals - float(q50)) / sc
        if invert:
            z = -z
        out[m] = np.clip(z, -4.5, 5.5)
    return out


def _shallow_mag_demag(
    tmi: np.ndarray,
    tmi_up150_u8: np.ndarray,
    blk_id: np.ndarray,
    foot: np.ndarray,
) -> np.ndarray:
    """Compute block-calibrated shallow (0-150 m) TMI magnetite-destruction deficit: -(TMI - fit(TMI_up150))."""
    deficit = np.zeros(tmi.shape, dtype=np.float32)
    up_f = tmi_up150_u8.astype(np.float32)
    for b in np.unique(blk_id[foot]):
        m = foot & (blk_id == b) & (tmi_up150_u8 > 0) & np.isfinite(tmi)
        if m.sum() < 200:
            continue
        x = up_f[m]
        y = tmi[m]
        xm, ym = float(x.mean()), float(y.mean())
        slope = float(np.dot(x - xm, y - ym) / (np.dot(x - xm, x - xm) + 1e-6))
        resid = y - (ym + slope * (x - xm))
        q25, q50, q75 = np.percentile(resid[::4], [25.0, 50.0, 75.0])
        sc = float(0.7413 * (q75 - q25)) + 1e-5
        # Negative TMI residual relative to 150m upward continuation = shallow demagnetization trough
        deficit[m] = np.clip(-(resid - float(q50)) / sc, -3.5, 6.0)
    return deficit


def _fractal_roughness_aniso(arr: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Real-band two-scale (200 m vs 800 m) directional variogram roughness x cross-strike anisotropy."""
    a = np.where(foot & np.isfinite(arr), arr, 0.0).astype(np.float32)
    p2 = np.pad(a, 2, mode="edge")
    h, w = a.shape
    dx2 = np.abs(p2[2 : h + 2, 4 : w + 4] - p2[2 : h + 2, 0:w])
    dy2 = np.abs(p2[4 : h + 4, 2 : w + 2] - p2[0:h, 2 : w + 2])
    del p2
    v_short = gaussian_filter(0.5 * (dx2 + dy2), sigma=2.0, mode="nearest")
    aniso = np.abs(dx2 - dy2) / (dx2 + dy2 + 1e-5)
    del dx2, dy2
    aniso_sm = gaussian_filter(aniso, sigma=2.5, mode="nearest")
    del aniso

    a_sub = a[::4, ::4]
    gy8, gx8 = np.gradient(gaussian_filter(a_sub, sigma=1.0, mode="nearest"))
    v_long_sub = np.hypot(gx8, gy8).astype(np.float32)
    v_long = zoom(v_long_sub, (h / a_sub.shape[0], w / a_sub.shape[1]), order=1).astype(np.float32)[:h, :w]

    # High local fine-scale increment energy sustained by directional anisotropy
    score = np.log1p(v_short / (np.percentile(v_short[foot][::8], 50.0) + 1e-5)) * (
        0.45 + 0.55 * aniso_sm
    ) * np.tanh(v_long / (np.percentile(v_long[foot][::8], 50.0) + 1e-5))
    score[~foot] = 0.0
    return udsr.robust_z(score, foot)


def build_sarpu_stack(ddir: Path, wdir: Path, force: bool = False, log=print) -> dict[str, Any]:
    """Build or open the 12-channel label-free H-SARPU physical feature stack memmap."""
    udsr_info = udsr.build_udsr_stack(ddir, wdir, force=False, log=log)
    foot = udsr_info["foot"]
    lid_valid = udsr_info["lidar_valid"]
    flat_playa = udsr_info["flat_deep_playa"]
    h, w = foot.shape

    out_path = wdir / "sarpu_stack_12.npy"
    meta_path = wdir / "sarpu_stack_12_meta.json"
    if out_path.exists() and meta_path.exists() and not force:
        return {
            "path": out_path,
            "channels": SARPU_CHANNELS,
            "foot": foot,
            "lidar_valid": lid_valid,
            "flat_deep_playa": flat_playa,
            "meta": json.loads(meta_path.read_text()),
        }

    bands_dir = wdir / "bands"
    ext = ddir / "external"
    mm = open_memmap(out_path, mode="w+", dtype=np.float32, shape=(h, w, len(SARPU_CHANNELS)))
    udsr_mm = open_memmap(wdir / "udsr_stack_18.npy", mode="r")

    z_base = udsr.load_band_clean(bands_dir / "15_depth_to_base_surf.npy", foot)
    slope = udsr.load_band_clean(bands_dir / "19_det_elev_slope.npy", foot)
    playa_gate = np.where(
        foot,
        1.0 - 0.88 * udsr.sigmoid_f32((z_base - 320.0) / 90.0) * udsr.sigmoid_f32((1.8 - slope) / 0.45),
        0.0,
    ).astype(np.float32)

    with rasterio.open(ext / "tiger_road_distance_m.tif") as ds_rd:
        d_road = np.nan_to_num(ds_rd.read(1), nan=1000.0).astype(np.float32)
    road_gate = (1.0 - 0.75 * np.exp(-((d_road / 150.0) ** 2))).astype(np.float32)
    del d_road

    with rasterio.open(ext / "acquisition_block_id_100m.tif") as ds_blk:
        blk_id = ds_blk.read(1)

    log("[H-SARPU] Stage 1/4: Shallow Mag Demag (TMI vs TMI_up150) & Baranov Pseudo-Gravity...")
    tmi = udsr.load_band_clean(bands_dir / "14_tmi.npy", foot)
    rtp = udsr.load_band_clean(bands_dir / "02_rtp.npy", foot)
    grav_hg = udsr.load_band_clean(bands_dir / "18_iso_grav_anom_hg.npy", foot)
    grav_gate = udsr.sigmoid_f32(udsr.robust_z(grav_hg, foot))

    with rasterio.open(ext / "geodawn_extensions_u8.tif") as ds_ext:
        thk_u8 = ds_ext.read(1)
        uk_u8 = ds_ext.read(2)
        uth_u8 = ds_ext.read(3)
        tmi_up150_u8 = ds_ext.read(4)

    demag_sh = _shallow_mag_demag(tmi, tmi_up150_u8, blk_id, foot)
    del tmi, tmi_up150_u8
    demag_ridge = np.maximum(features._hessian_ridge(gaussian_filter(demag_sh, sigma=1.1, mode="nearest"), 1.6), 0.0)
    mm[:, :, 0] = udsr.robust_z((0.55 * np.maximum(demag_sh, 0.0) + 0.45 * udsr.robust_z(demag_ridge, foot)) * grav_gate * playa_gate, foot)
    del demag_sh, demag_ridge

    pg_grad = _baranov_pseudogravity_grad(rtp, foot)
    baranov_def = np.maximum(udsr.robust_z(grav_hg, foot) - 0.60 * udsr.robust_z(pg_grad, foot), 0.0) * grav_gate * playa_gate
    mm[:, :, 1] = udsr.robust_z(baranov_def, foot)
    del pg_grad, baranov_def

    log("[H-SARPU] Stage 2/4: GeoDAWN Th/K Adularia, U/K+U/Th Radon & BLM Epithermal Claims...")
    thk_inv = _block_standardize_u8(thk_u8, blk_id, foot, invert=True)  # low Th/K = K-metasomatism
    del thk_u8
    thk_ridge = np.maximum(features._hessian_ridge(gaussian_filter(thk_inv, sigma=1.2, mode="nearest"), 1.8), 0.0)
    mm[:, :, 2] = udsr.robust_z((0.50 * np.maximum(thk_inv, 0.0) + 0.50 * udsr.robust_z(thk_ridge, foot)) * road_gate * playa_gate, foot)
    del thk_inv, thk_ridge

    uk_z = _block_standardize_u8(uk_u8, blk_id, foot, invert=False)
    uth_z = _block_standardize_u8(uth_u8, blk_id, foot, invert=False)
    del uk_u8, uth_u8, blk_id
    radon_comb = 0.50 * uk_z + 0.50 * uth_z
    del uk_z, uth_z
    radon_ridge = np.maximum(features._hessian_ridge(gaussian_filter(radon_comb, sigma=1.2, mode="nearest"), 1.8), 0.0)
    mm[:, :, 3] = udsr.robust_z((0.45 * np.maximum(radon_comb, 0.0) + 0.55 * udsr.robust_z(radon_ridge, foot)) * road_gate * playa_gate, foot)
    del radon_comb, radon_ridge

    cond = udsr.load_band_clean(bands_dir / "17_cond_surf.npy", foot)
    cy_c, cx_c = np.gradient(gaussian_filter(np.log1p(np.maximum(cond, 0.0)), sigma=1.5, mode="nearest"))
    cond_grad_gate = udsr.sigmoid_f32(udsr.robust_z(np.hypot(cx_c, cy_c), foot))
    del cy_c, cx_c

    with rasterio.open(ext / "blm_closed_claim_distance_m.tif") as ds_blm:
        d_blm = np.nan_to_num(ds_blm.read(1), nan=15000.0).astype(np.float32)
    blm_prox = (0.65 * np.exp(-d_blm / 450.0) + 0.35 * np.exp(-d_blm / 1400.0)).astype(np.float32)
    del d_blm
    subsurf_root = (0.55 * grav_gate + 0.45 * cond_grad_gate).astype(np.float32)
    mm[:, :, 4] = udsr.robust_z(blm_prox * subsurf_root * road_gate * playa_gate, foot)
    del blm_prox, cond_grad_gate
    mm.flush()
    udsr._drop_mm_cache(mm)
    gc.collect()

    log("[H-SARPU] Stage 3/4: Anisotropic Darcy Plume, Biot-Seis Potency, Profile Scarp & Real Fractal...")
    grav = udsr.load_band_clean(bands_dir / "13_iso_grav_anom.npy", foot)
    gy_g, gx_g = np.gradient(gaussian_filter(grav, sigma=2.0, mode="nearest"))
    gy_m, gx_m = np.gradient(gaussian_filter(rtp, sigma=2.0, mode="nearest"))
    # Average structure-tensor normal to obtain local subsurface strike tangent t = (-ny, nx)
    ng = np.hypot(gx_g, gy_g) + 1e-6
    nm = np.hypot(gx_m, gy_m) + 1e-6
    c2 = 0.60 * ((gx_g / ng) ** 2 - (gy_g / ng) ** 2) + 0.40 * ((gx_m / nm) ** 2 - (gy_m / nm) ** 2)
    s2 = 0.60 * (2.0 * gx_g * gy_g / (ng * ng)) + 0.40 * (2.0 * gx_m * gy_m / (nm * nm))
    del gx_g, gy_g, gx_m, gy_m, ng, nm
    theta_grad = 0.5 * np.arctan2(s2, c2 + 1e-12)
    theta_pf_strike = (theta_grad + 0.5 * np.pi).astype(np.float32)
    tx_pf = np.cos(theta_pf_strike).astype(np.float32)
    ty_pf = np.sin(theta_pf_strike).astype(np.float32)
    del c2, s2, theta_grad

    plume_sio2, plume_probe, _ = udsr._rasterize_external_hydrothermal(ddir, foot)
    src_therm = (0.55 * np.maximum(udsr.robust_z(plume_sio2, foot), 0.0) + 0.45 * np.maximum(udsr.robust_z(plume_probe, foot), 0.0)).astype(np.float32)
    del plume_sio2, plume_probe
    aniso_plume = _anisotropic_strike_plume(src_therm, tx_pf, ty_pf, foot)
    del src_therm, tx_pf, ty_pf
    mm[:, :, 5] = udsr.robust_z(aniso_plume * (0.35 + 0.65 * subsurf_root) * playa_gate, foot)
    del aniso_plume, subsurf_root

    geod_sh = udsr.load_band_clean(bands_dir / "07_geod_shearrate.npy", foot)
    geod_dil = udsr.load_band_clean(bands_dir / "08_geod_dilaterate.npy", foot)
    deq = udsr.load_band_clean(bands_dir / "10_deq_n100a15.npy", foot)
    ieq = udsr.load_band_clean(bands_dir / "16_ieq_n100a15.npy", foot)
    seis_log = 0.60 * udsr.robust_z(np.log1p(np.maximum(ieq, 0.0)), foot) + 0.40 * udsr.robust_z(np.log1p(np.maximum(deq, 0.0)), foot)
    del deq, ieq
    pied_win = np.exp(-((np.log(np.maximum(z_base, 20.0) / 240.0)) ** 2) / 2.2).astype(np.float32)
    biot = (
        udsr.sigmoid_f32(udsr.robust_z(geod_sh, foot))
        * udsr.sigmoid_f32(0.7 * udsr.robust_z(geod_dil, foot) + 0.5 * udsr.robust_z(cond, foot))
        * udsr.sigmoid_f32(seis_log)
        * (0.45 + 0.55 * pied_win)
        * playa_gate
    )
    del geod_sh, geod_dil, cond, seis_log, pied_win
    mm[:, :, 6] = udsr.robust_z(biot, foot)
    del biot

    det_elev = udsr.load_band_clean(bands_dir / "12_det_elev.npy", foot)
    ez_y, ez_x = np.gradient(gaussian_filter(det_elev, sigma=1.2, mode="nearest"))
    ez_n = np.hypot(ez_x, ez_y) + 1e-5
    ey_yy, ey_yx = np.gradient(ez_y)
    ex_xy, ex_xx = np.gradient(ez_x)
    # Profile curvature along steepest descent: captures scarp crest/toe break seamlessly in 100m DEM
    prof_curv = np.abs(ex_xx * (ez_x / ez_n) ** 2 + 2.0 * ex_xy * (ez_x * ez_y) / (ez_n * ez_n) + ey_yy * (ez_y / ez_n) ** 2)
    del ez_x, ez_y, ez_n, ey_yy, ey_yx, ex_xy, ex_xx
    shore_suppress = np.where((z_base > 170.0) & (slope < 3.2) & (grav_gate < 0.48), 0.30, 1.0).astype(np.float32)
    mm[:, :, 7] = udsr.robust_z(prof_curv * udsr.sigmoid_f32(udsr.robust_z(slope, foot)) * road_gate * shore_suppress * playa_gate, foot)
    del prof_curv, z_base, slope

    frac_dem = _fractal_roughness_aniso(det_elev, foot)
    frac_rtp = _fractal_roughness_aniso(rtp, foot)
    frac_grv = _fractal_roughness_aniso(grav, foot)
    del det_elev, rtp, grav, grav_hg
    mm[:, :, 8] = udsr.robust_z((0.40 * frac_dem + 0.32 * frac_rtp + 0.28 * frac_grv) * road_gate * playa_gate, foot)
    del frac_dem, frac_rtp, frac_grv
    mm.flush()
    udsr._drop_mm_cache(mm)
    gc.collect()

    log("[H-SARPU] Stage 4/4: Wallace LiDAR Scarp-Dipole, LiDAR-PF Strike Concordance & Blind Index...")
    with rasterio.open(ext / "lidar_scarp_features_u8.tif") as ds_lid:
        ex_max = ds_lid.read(1).astype(np.float32) / 255.0
        lapneg = ds_lid.read(4).astype(np.float32) / 255.0
        lappos = ds_lid.read(5).astype(np.float32) / 255.0
        downf = ds_lid.read(6).astype(np.float32) / 255.0
        upf = ds_lid.read(7).astype(np.float32) / 255.0
        cross_m = ds_lid.read(8).astype(np.float32) / 255.0
        lid_strike = (ds_lid.read(11).astype(np.float32) / 255.0) * np.float32(np.pi)

    dipole = np.sqrt(np.maximum(lapneg * lappos, 0.0)) * (0.65 * downf + 0.35 * upf) * road_gate * shore_suppress * playa_gate
    del lapneg, lappos, downf, upf
    dipole = np.where(lid_valid, dipole, 0.0).astype(np.float32)
    mm[:, :, 9] = np.where(lid_valid, udsr.robust_z(dipole, lid_valid), 0.0)
    del dipole

    cos2_concord = np.cos(lid_strike - theta_pf_strike) ** 2
    del lid_strike, theta_pf_strike
    concord = np.sqrt(np.maximum(ex_max * cross_m, 0.0)) * (0.25 + 0.75 * cos2_concord) * road_gate * shore_suppress * playa_gate
    del ex_max, cross_m, cos2_concord, road_gate, shore_suppress
    concord = np.where(lid_valid, concord, 0.0).astype(np.float32)
    mm[:, :, 10] = np.where(lid_valid, udsr.robust_z(concord, lid_valid), 0.0)
    del concord

    # Channel 11: 100% DEM-slope-free and 1m-LiDAR-free pure-subsurface blind geothermal conduit index [0, 1]
    updip_grav = np.array(udsr_mm[:, :, 2], dtype=np.float32, copy=True)
    updip_mt = np.array(udsr_mm[:, :, 4], dtype=np.float32, copy=True)
    gallardo = np.array(udsr_mm[:, :, 5], dtype=np.float32, copy=True)
    udsr._drop_mm_cache(udsr_mm)
    raw_blind = (
        0.22 * udsr.rank01(updip_grav, foot)
        + 0.20 * udsr.rank01(mm[:, :, 1], foot)
        + 0.16 * udsr.rank01(mm[:, :, 0], foot)
        + 0.14 * udsr.rank01(updip_mt, foot)
        + 0.10 * udsr.rank01(gallardo, foot)
        + 0.08 * udsr.rank01(mm[:, :, 5], foot)
        + 0.05 * udsr.rank01(mm[:, :, 4], foot)
        + 0.05 * udsr.rank01(0.5 * mm[:, :, 2] + 0.5 * mm[:, :, 3], foot)
    ) * playa_gate
    del updip_grav, updip_mt, gallardo, playa_gate
    mm[:, :, 11] = udsr.oriented_nms_4az(udsr.rank01(raw_blind, foot), foot, blend=0.42)
    del raw_blind

    mm.flush()
    udsr._drop_mm_cache(mm)
    del mm
    gc.collect()

    meta = {
        "n_channels": len(SARPU_CHANNELS),
        "channels": list(SARPU_CHANNELS),
        "lidar_valid_px": int(lid_valid.sum()),
        "flat_deep_playa_px": int(flat_playa.sum()),
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    log(f"[H-SARPU] Saved {out_path.name} ({len(SARPU_CHANNELS)} channels)")
    return {
        "path": out_path,
        "channels": SARPU_CHANNELS,
        "foot": foot,
        "lidar_valid": lid_valid,
        "flat_deep_playa": flat_playa,
        "meta": meta,
    }


def _build_williams_lobe_templates(radius: int = 20, n_az: int = 16) -> np.ndarray:
    """Precompute 16 azimuth-quantized Williams (1957) Mode-I + +/-35 deg wing-crack tensile kernels."""
    yy, xx = np.mgrid[-radius : radius + 1, -radius : radius + 1].astype(np.float32)
    rr = np.hypot(yy, xx)
    radial = np.where((rr >= 1.5) & (rr <= float(radius)), (1.0 / np.sqrt(1.0 + rr / 2.5)) * np.exp(-rr / 10.5), 0.0)
    ang_grid = np.arctan2(yy, xx)
    bank = np.zeros((n_az, 2 * radius + 1, 2 * radius + 1), dtype=np.float32)
    wing_rad = np.deg2rad(35.0)
    wing_sig = np.deg2rad(18.0)
    max_half = np.deg2rad(78.0)
    for k in range(n_az):
        phi = -np.pi + (2.0 * np.pi * k) / n_az
        da = np.abs((ang_grid - phi + np.pi) % (2.0 * np.pi) - np.pi)
        coplanar = np.where(da < max_half, np.maximum(np.cos(0.5 * da), 0.0) ** 3, 0.0)
        wing = 0.85 * np.exp(-((da - wing_rad) ** 2) / (2.0 * wing_sig * wing_sig))
        bank[k] = (radial * np.maximum(coplanar, wing)).astype(np.float32)
    return bank


_WILLIAMS_RADIUS = 20
_WILLIAMS_N_AZ = 16
_WILLIAMS_BANK = _build_williams_lobe_templates(_WILLIAMS_RADIUS, _WILLIAMS_N_AZ)


def compute_lefm_continuation(visible_mask: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Compute 2 bounded [0, 1] LEFM fracture-mechanics channels STRICTLY from ``visible_mask``.

    Channel 0: Williams (1957) / Pollard & Segall (1987) coplanar + +/-35 deg wing-crack tensile stress.
    Channel 1: Crider & Pollard (1998) en-echelon relay-ramp breaching interaction stress.
    """
    vis = np.asarray(visible_mask, bool) & foot
    h, w = foot.shape
    out = np.zeros((h, w, 2), dtype=np.float32)
    if not vis.any():
        return out

    # 1. Williams (1957) Mode-I/II fault-termination tensile lobes
    # Exact discrete-geometry tip detector on 1-px skeletons + 2-px end-hooks (excludes interior bends)
    p = np.pad(vis.astype(np.int16), 1, mode="constant")
    nbr8 = np.zeros((h, w), dtype=np.int16)
    sdy = np.zeros((h, w), dtype=np.int16)
    sdx = np.zeros((h, w), dtype=np.int16)
    for dy_k in (-1, 0, 1):
        for dx_k in (-1, 0, 1):
            if dy_k == 0 and dx_k == 0:
                continue
            sl_k = p[1 + dy_k : h + 1 + dy_k, 1 + dx_k : w + 1 + dx_k]
            nbr8 += sl_k
            sdy += dy_k * sl_k
            sdx += dx_k * sl_k
    del p
    tips = vis & ((nbr8 == 1) | ((nbr8 == 2) & ((sdy * sdy + sdx * sdx) >= 4)))
    del nbr8, sdy, sdx
    ty, tx = np.nonzero(tips)
    rad = _WILLIAMS_RADIUS
    w_field = np.zeros((h + 2 * rad, w + 2 * rad), dtype=np.float32)

    for y0, x0 in zip(ty, tx):
        r0, r1 = max(0, int(y0) - 6), min(h, int(y0) + 7)
        c0, c1 = max(0, int(x0) - 6), min(w, int(x0) + 7)
        wy, wx = np.nonzero(vis[r0:r1, c0:c1])
        if wy.size < 3:
            continue
        dy = (wy + r0 - float(y0)).astype(np.float32)
        dx = (wx + c0 - float(x0)).astype(np.float32)
        cy, cx = float(dy.mean()), float(dx.mean())
        nrm = float(np.hypot(cy, cx))
        if nrm < 0.25:
            cov_yy = float((dy * dy).mean())
            cov_xx = float((dx * dx).mean())
            cov_yx = float((dy * dx).mean())
            ang = 0.5 * float(np.arctan2(2.0 * cov_yx, cov_xx - cov_yy + 1e-6))
            az_list = (ang, float((ang + np.pi) % (2.0 * np.pi) - np.pi))
        else:
            az_list = (float(np.arctan2(-cy, -cx)),)
        # Weight longer segments slightly stronger (sqrt scaling capped)
        seg_wt = np.float32(min(1.35, 0.55 + 0.16 * np.sqrt(float(wy.size))))
        py_c, px_c = int(y0) + rad, int(x0) + rad
        sub = w_field[py_c - rad : py_c + rad + 1, px_c - rad : px_c + rad + 1]
        for az in az_list:
            bin_k = int(round(((az + np.pi) / (2.0 * np.pi)) * _WILLIAMS_N_AZ)) % _WILLIAMS_N_AZ
            np.maximum(sub, seg_wt * _WILLIAMS_BANK[bin_k], out=sub)

    lobe = gaussian_filter(w_field[rad : h + rad, rad : w + rad], sigma=1.1, mode="constant")
    del w_field
    sc_w = float(np.percentile(lobe[foot][::4], 99.5)) + 1e-6
    out[:, :, 0] = np.where(foot, np.clip(lobe / sc_w, 0.0, 1.0), 0.0)
    del lobe

    # 2. Crider & Pollard (1998) two-segment relay-ramp breaching potential
    comp, n_comp = label(vis, structure=np.ones((3, 3), dtype=int))
    if n_comp <= 1:
        return out
    d1_sub = distance_transform_edt(~vis[::2, ::2]).astype(np.float32) * 2.0
    d1 = zoom(d1_sub, (h / d1_sub.shape[0], w / d1_sub.shape[1]), order=1).astype(np.float32)[:h, :w]
    d2 = udsr.exact_second_component_edt(comp, downsample=2)
    del comp, d1_sub

    # Relay peaks between two distinct segments (small d1+d2 AND balanced |d1-d2|)
    relay = (
        np.exp(-(d1 + d2) / 16.5)
        * np.exp(-np.abs(d1 - d2) / 9.5)
        * (1.0 - 0.55 * np.exp(-np.maximum(d1, d2) / 2.2))
    )
    del d1, d2
    sc_r = float(np.percentile(relay[foot][::4], 99.5)) + 1e-6
    out[:, :, 1] = np.where(foot, np.clip(relay / sc_r, 0.0, 1.0), 0.0)
    return out


def sample_isomorphic_lefm_dataset(
    train_domain: np.ndarray,
    visible_mask: np.ndarray,
    foot: np.ndarray,
    n_groups: int = 5,
    max_pos: int = 30000,
    max_unlab: int = 95000,
    seed: int = 20261028,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate train-test-isomorphic 5-fold component-withheld samples for Coupled LEFM + SAR-PU.

    In each fold ``g in 0..n_groups-1``, 20% of connected fault segments ``vis_g`` are withheld and
    LEFM continuation is computed strictly from the remaining 80% ``vis_minus_g`` (identical to
    ``HoldoutContext(hide_frac=0.20)``). Positives are ``vis_g & (d(vis_minus_g) > 2.0)`` and
    unlabeled samples are ``(~vis) & (d(vis_minus_g) > 2.0)`` spanning the full ``d > 2.0`` domain.
    """
    vis = np.asarray(visible_mask, bool) & foot
    h, w = foot.shape
    comp, n_comp = label(vis, structure=np.ones((3, 3), dtype=int))
    rng = np.random.default_rng(seed)

    if n_comp == 0:
        py, px = np.nonzero(vis & train_domain)
        uy, ux = np.nonzero((~vis) & train_domain)
        return (
            py[:max_pos], px[:max_pos], np.zeros((min(py.size, max_pos), 2), np.float32),
            uy[:max_unlab], ux[:max_unlab], np.zeros((min(uy.size, max_unlab), 2), np.float32),
        )

    comp_group = np.zeros(n_comp + 1, dtype=np.int8)
    comp_group[1:] = rng.integers(0, n_groups, size=n_comp, dtype=np.int8)

    pos_ys, pos_xs, pos_lefms = [], [], []
    un_ys, un_xs, un_lefms = [], [], []
    per_fold_pos = max(1, max_pos // n_groups)
    per_fold_un = max(1, max_unlab // n_groups)

    for g in range(n_groups):
        keep_lut = comp_group != g
        keep_lut[0] = False
        hold_lut = comp_group == g
        hold_lut[0] = False

        vis_minus_g = keep_lut[comp]
        vis_in_g = hold_lut[comp]

        d_sub = distance_transform_edt(~vis_minus_g[::2, ::2]).astype(np.float32) * 2.0
        d_g = zoom(d_sub, (h / d_sub.shape[0], w / d_sub.shape[1]), order=1).astype(np.float32)[:h, :w]
        del d_sub

        lefm_g = compute_lefm_continuation(vis_minus_g, foot)
        del vis_minus_g

        p_mask = vis_in_g & train_domain & (d_g > 2.0)
        py_g, px_g = np.nonzero(p_mask)
        if py_g.size > per_fold_pos:
            ip = rng.choice(py_g.size, per_fold_pos, replace=False)
            py_g, px_g = py_g[ip], px_g[ip]
        pos_ys.append(py_g)
        pos_xs.append(px_g)
        pos_lefms.append(lefm_g[py_g, px_g, :])

        # Sample both collar (2 < d_g <= 15) and far-basin (d_g > 15) unlabeled background
        u_near_y, u_near_x = np.nonzero((~vis) & train_domain & (d_g > 2.0) & (d_g <= 15.0))
        u_far_y, u_far_x = np.nonzero((~vis) & train_domain & (d_g > 15.0))
        n_near = min(u_near_y.size, int(0.42 * per_fold_un))
        n_far = min(u_far_y.size, per_fold_un - n_near)
        if n_near > 0:
            in_idx = rng.choice(u_near_y.size, n_near, replace=False)
            un_ys.append(u_near_y[in_idx])
            un_xs.append(u_near_x[in_idx])
            un_lefms.append(lefm_g[u_near_y[in_idx], u_near_x[in_idx], :])
        if n_far > 0:
            if_idx = rng.choice(u_far_y.size, n_far, replace=False)
            un_ys.append(u_far_y[if_idx])
            un_xs.append(u_far_x[if_idx])
            un_lefms.append(lefm_g[u_far_y[if_idx], u_far_x[if_idx], :])

        del vis_in_g, d_g, lefm_g

    del comp
    return (
        np.concatenate(pos_ys),
        np.concatenate(pos_xs),
        np.vstack(pos_lefms).astype(np.float32),
        np.concatenate(un_ys),
        np.concatenate(un_xs),
        np.vstack(un_lefms).astype(np.float32),
    )


def extract_phys65_sorted(
    ys: np.ndarray,
    xs: np.ndarray,
    base_mm: np.ndarray,
    udsr_mm: np.ndarray,
    sarpu_mm: np.ndarray,
    batch: int = 25000,
) -> np.ndarray:
    """Sequential-friendly batched memmap gather of all 65 pure-physical channels."""
    n = ys.size
    out = np.empty((n, 65), dtype=np.float32)
    order = np.argsort(ys, kind="mergesort")
    ys_s, xs_s = ys[order], xs[order]
    tmp = np.empty((n, 65), dtype=np.float32)
    for s in range(0, n, batch):
        e = min(n, s + batch)
        yb, xb = ys_s[s:e], xs_s[s:e]
        tmp[s:e, 0:35] = np.nan_to_num(base_mm[yb, xb, :], nan=0.0)
        tmp[s:e, 35:53] = np.nan_to_num(udsr_mm[yb, xb, :], nan=0.0)
        tmp[s:e, 53:65] = np.nan_to_num(sarpu_mm[yb, xb, :], nan=0.0)
        udsr._drop_mm_cache(base_mm)
        udsr._drop_mm_cache(udsr_mm)
        udsr._drop_mm_cache(sarpu_mm)
    out[order] = tmp
    return out


def run_leakage_canary_67(
    base_mm: np.ndarray,
    udsr_mm: np.ndarray,
    sarpu_mm: np.ndarray,
    ctx: Any,
    max_auc_threshold: float = 0.90,
    seed: int = 20261028,
) -> dict[str, Any]:
    """Protocol Rule 4 Leakage Canary across ALL 67 channels (35 base + 18 udsr + 12 sarpu + 2 LEFM)."""
    rng = np.random.default_rng(seed)
    pos_rows, neg_rows = [], []

    for cell in ctx.cells:
        sl = cell.bbox
        lefm_full = compute_lefm_continuation(cell.visible_full, ctx.foot)
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
        gy_p, gx_p = py + r0, px + c0
        gy_n, gx_n = ny + r0, nx + c0
        xp65 = extract_phys65_sorted(gy_p, gx_p, base_mm, udsr_mm, sarpu_mm)
        xn65 = extract_phys65_sorted(gy_n, gx_n, base_mm, udsr_mm, sarpu_mm)
        pos_rows.append(np.hstack([xp65, lefm_full[gy_p, gx_p, :]]))
        neg_rows.append(np.hstack([xn65, lefm_full[gy_n, gx_n, :]]))
        del lefm_full, xp65, xn65
        gc.collect()

    X_pos = np.vstack(pos_rows)
    X_neg = np.vstack(neg_rows)
    y = np.concatenate([np.ones(len(X_pos), dtype=np.int8), np.zeros(len(X_neg), dtype=np.int8)])
    X = np.vstack([X_pos, X_neg])

    all_names = list(features.CHANNELS) + list(udsr.UDSR_CHANNELS) + list(SARPU_CHANNELS) + list(LEFM_CHANNELS)
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

    return {
        "passed": bool(worst_auc <= max_auc_threshold),
        "threshold": max_auc_threshold,
        "n_features_tested": len(all_names),
        "n_pos_sampled": int(len(X_pos)),
        "n_neg_sampled": int(len(X_neg)),
        "max_oriented_auc": round(worst_auc, 6),
        "worst_channel": worst_name,
        "aucs": aucs,
    }


def _estimate_sar_propensity_weights(
    X_pos: np.ndarray,
    lid_pos: np.ndarray,
    X_unlab: np.ndarray,
    lid_unlab: np.ndarray,
) -> np.ndarray:
    """Estimate clipped inverse observation-propensity weights w_+(x) = clip(mean(e_+)/e(x), 0.75, 2.85).

    Models the Great Basin scarp-observation selection mechanism P(S=1 | x_obs) from exposure
    covariates only (det_elev_slope, relief5, tophat2, depth_to_base_surf, piedmont_locus, lidar_valid).
    Low-relief / buried positives receive higher weight than over-represented steep LiDAR scarps.
    """
    Xp_obs = np.column_stack([X_pos[:, PROPENSITY_COLS_65], lid_pos.astype(np.float32)])
    Xu_obs = np.column_stack([X_unlab[:, PROPENSITY_COLS_65], lid_unlab.astype(np.float32)])
    X_obs = np.vstack([Xp_obs, Xu_obs])
    y_obs = np.concatenate([np.ones(len(Xp_obs), dtype=np.int8), np.zeros(len(Xu_obs), dtype=np.int8)])

    scaler = StandardScaler()
    X_std = np.clip(scaler.fit_transform(X_obs), -5.0, 5.0)
    lr = LogisticRegression(C=0.25, max_iter=200)
    lr.fit(X_std, y_obs)
    e_pos = np.clip(lr.predict_proba(X_std[: len(Xp_obs)])[:, 1], 0.04, 0.96)
    e_ref = float(np.median(e_pos))
    w_pos = np.clip(e_ref / e_pos, 0.75, 2.85).astype(np.float32)
    return w_pos


class MultiFamilyEnsemble:
    """Fast Cython-vectorized column-subsampled L2 HistGradientBoosting wrapper."""

    def __init__(self, hgb: HistGradientBoostingClassifier):
        self.hgb = hgb

    def predict_proba_1(self, X: np.ndarray) -> np.ndarray:
        return self.hgb.predict_proba(X)[:, 1].astype(np.float32)


def _fit_sarpu_pair(
    Xp: np.ndarray,
    wp: np.ndarray,
    lid_p: np.ndarray,
    Xu: np.ndarray,
    blind_u: np.ndarray,
    lid_u: np.ndarray,
    non_lidar_cols: tuple[int, ...],
    seed: int,
) -> tuple[MultiFamilyEnsemble, MultiFamilyEnsemble]:
    """Two-stage reliable-negative SAR-PU training for M_Gap (non-LiDAR) and M_Full (LiDAR-valid)."""
    # Stage 1 pilot on non-LiDAR columns to identify likely unmapped blind faults contaminating U
    X_pilot = np.vstack([Xp[:, non_lidar_cols], Xu[:, non_lidar_cols]])
    y_pilot = np.concatenate([np.ones(len(Xp), dtype=np.int8), np.zeros(len(Xu), dtype=np.int8)])
    w_pilot = np.concatenate([wp, np.ones(len(Xu), dtype=np.float32)])
    pilot = HistGradientBoostingClassifier(
        max_iter=75, learning_rate=0.08, max_leaf_nodes=31, min_samples_leaf=100,
        max_features=0.75, l2_regularization=3.0, random_state=seed,
    )
    pilot.fit(X_pilot, y_pilot, sample_weight=w_pilot)
    p_u = pilot.predict_proba(Xu[:, non_lidar_cols])[:, 1].astype(np.float32)
    del X_pilot, y_pilot, w_pilot, pilot

    # Excise top 4% pilot unlabeled fault candidates + top 3% pure-subsurface blind conduits from y=0
    q96_pilot = float(np.percentile(p_u, 96.0))
    q97_blind = float(np.percentile(blind_u, 97.0))
    reliable_u = (p_u < q96_pilot) & (blind_u < q97_blind)
    wu_rel = np.clip(1.0 - 0.55 * (p_u[reliable_u] / max(q96_pilot, 1e-4)), 0.35, 1.0).astype(np.float32)
    Xu_rel = Xu[reliable_u]
    lid_u_rel = lid_u[reliable_u]

    # 1. Fit M_Gap on all reliable samples using strictly 1m-LiDAR-free columns
    Xg = np.vstack([Xp[:, non_lidar_cols], Xu_rel[:, non_lidar_cols]])
    yg = np.concatenate([np.ones(len(Xp), dtype=np.int8), np.zeros(len(Xu_rel), dtype=np.int8)])
    wg = np.concatenate([wp, wu_rel])

    hgb_g = HistGradientBoostingClassifier(
        max_iter=155, learning_rate=0.06, max_leaf_nodes=35, min_samples_leaf=90,
        max_features=0.75, l2_regularization=3.0, random_state=seed + 11,
    )
    hgb_g.fit(Xg, yg, sample_weight=wg)
    del Xg, yg, wg

    # 2. Fit M_Full inside lidar_valid on all columns
    Xp_f, wp_f = Xp[lid_p], wp[lid_p]
    Xu_f, wu_f = Xu_rel[lid_u_rel], wu_rel[lid_u_rel]
    Xf = np.vstack([Xp_f, Xu_f])
    yf = np.concatenate([np.ones(len(Xp_f), dtype=np.int8), np.zeros(len(Xu_f), dtype=np.int8)])
    wf = np.concatenate([wp_f, wu_f])

    hgb_f = HistGradientBoostingClassifier(
        max_iter=155, learning_rate=0.06, max_leaf_nodes=35, min_samples_leaf=90,
        max_features=0.75, l2_regularization=3.0, random_state=seed + 37,
    )
    hgb_f.fit(Xf, yf, sample_weight=wf)
    del Xf, yf, wf
    return MultiFamilyEnsemble(hgb_f), MultiFamilyEnsemble(hgb_g)


def fit_sarpu_dual_systems(
    train_domain: np.ndarray,
    visible_faults: np.ndarray,
    foot: np.ndarray,
    lidar_valid: np.ndarray,
    base_mm: np.ndarray,
    udsr_mm: np.ndarray,
    sarpu_mm: np.ndarray,
    seed: int = 20261028,
) -> dict[str, Any]:
    """Fit BOTH pure-physical SAR-PU Dual-Cover AND 5-group-jackknifed Coupled LEFM+SAR-PU Dual-Cover."""
    rng = np.random.default_rng(seed)
    h, w = visible_faults.shape
    d_sub = distance_transform_edt(~visible_faults[::2, ::2]).astype(np.float32) * 2.0
    d_vis = zoom(d_sub, (h / d_sub.shape[0], w / d_sub.shape[1]), order=1).astype(np.float32)[:h, :w]
    del d_sub

    pos_all = visible_faults & train_domain
    unlab_all = train_domain & (d_vis > 4.0)

    py, px = np.nonzero(pos_all)
    uy, ux = np.nonzero(unlab_all)
    if py.size > 30000:
        ip = rng.choice(py.size, 30000, replace=False)
        py, px = py[ip], px[ip]
    n_u = min(uy.size, max(92000, 3 * py.size))
    iu = rng.choice(uy.size, n_u, replace=False)
    uy, ux = uy[iu], ux[iu]

    Xp65 = extract_phys65_sorted(py, px, base_mm, udsr_mm, sarpu_mm)
    Xu65 = extract_phys65_sorted(uy, ux, base_mm, udsr_mm, sarpu_mm)
    lid_p = lidar_valid[py, px]
    lid_u = lidar_valid[uy, ux]
    blind_u = Xu65[:, 64]  # channel 64 = sarpu_blind_conduit_index

    wp = _estimate_sar_propensity_weights(Xp65, lid_p, Xu65, lid_u)

    # System A: Pure-physical SAR-PU Dual-Cover (65 / 60 channels — zero catalogue features)
    pure_full, pure_gap = _fit_sarpu_pair(
        Xp65, wp, lid_p, Xu65, blind_u, lid_u, NON_LIDAR_COLS_65, seed=seed
    )
    del Xp65, Xu65, wp, lid_p, lid_u, blind_u
    gc.collect()

    # System B: Train-test-isomorphic 5-fold component-withheld LEFM + SAR-PU (67 / 62 channels)
    py_c, px_c, lefm_p, uy_c, ux_c, lefm_u = sample_isomorphic_lefm_dataset(
        train_domain, visible_faults, foot, n_groups=5, max_pos=30000, max_unlab=95000, seed=seed + 7
    )
    Xp65_c = extract_phys65_sorted(py_c, px_c, base_mm, udsr_mm, sarpu_mm)
    Xu65_c = extract_phys65_sorted(uy_c, ux_c, base_mm, udsr_mm, sarpu_mm)
    lid_pc = lidar_valid[py_c, px_c]
    lid_uc = lidar_valid[uy_c, ux_c]
    blind_uc = Xu65_c[:, 64]
    wp_c_raw = _estimate_sar_propensity_weights(Xp65_c, lid_pc, Xu65_c, lid_uc)
    wp_coup = (0.60 + 0.40 * wp_c_raw).astype(np.float32)

    Xp67 = np.hstack([Xp65_c, lefm_p])
    Xu67 = np.hstack([Xu65_c, lefm_u])
    del Xp65_c, Xu65_c, lefm_p, lefm_u, py_c, px_c, uy_c, ux_c, wp_c_raw
    coup_full, coup_gap = _fit_sarpu_pair(
        Xp67, wp_coup, lid_pc, Xu67, blind_uc, lid_uc, NON_LIDAR_COLS_67, seed=seed + 200
    )
    del Xp67, Xu67, wp_coup, lid_pc, lid_uc, blind_uc
    gc.collect()

    # Quantile calibration tables aligning M_Gap onto M_Full inside held-in lidar_valid & d_vis > 2
    cal_y, cal_x = np.nonzero(train_domain & lidar_valid & (d_vis > 2.0))
    if cal_y.size > 20000:
        ic = rng.choice(cal_y.size, 20000, replace=False)
        cal_y, cal_x = cal_y[ic], cal_x[ic]
    X_cal65 = extract_phys65_sorted(cal_y, cal_x, base_mm, udsr_mm, sarpu_mm)
    lefm_cal_full = compute_lefm_continuation(visible_faults, foot)
    X_cal67 = np.hstack([X_cal65, lefm_cal_full[cal_y, cal_x, :]])
    del lefm_cal_full, d_vis

    qs = np.linspace(0.0, 100.0, 201)
    pf_p = pure_full.predict_proba_1(X_cal65)
    pg_p = pure_gap.predict_proba_1(X_cal65[:, NON_LIDAR_COLS_65])
    q_pure = np.vstack([np.percentile(pg_p, qs), np.percentile(pf_p, qs)]).astype(np.float32)

    pf_c = coup_full.predict_proba_1(X_cal67)
    pg_c = coup_gap.predict_proba_1(X_cal67[:, NON_LIDAR_COLS_67])
    q_coup = np.vstack([np.percentile(pg_c, qs), np.percentile(pf_c, qs)]).astype(np.float32)
    del X_cal65, X_cal67
    gc.collect()

    return {
        "pure_full": pure_full,
        "pure_gap": pure_gap,
        "q_pure": q_pure,
        "coup_full": coup_full,
        "coup_gap": coup_gap,
        "q_coup": q_coup,
    }


def predict_sarpu_dual_bbox(
    bbox: tuple[slice, slice],
    eval_mask_sub: np.ndarray,
    lidar_valid: np.ndarray,
    base_mm: np.ndarray,
    udsr_mm: np.ndarray,
    sarpu_mm: np.ndarray,
    lefm_sub: np.ndarray,
    models: dict[str, Any],
    row_strip: int = 256,
) -> tuple[np.ndarray, np.ndarray]:
    """Strip-streaming prediction returning BOTH (p_pure_sub, p_coupled_sub) with < 250 MB strip RAM."""
    r0 = int(bbox[0].start)
    c0, c1 = int(bbox[1].start), int(bbox[1].stop)
    sh, sw = eval_mask_sub.shape
    p_pure = np.zeros((sh, sw), dtype=np.float32)
    p_coup = np.zeros((sh, sw), dtype=np.float32)
    lid_sub = lidar_valid[bbox]

    q_pure = models["q_pure"]
    q_coup = models["q_coup"]

    for sr0 in range(0, sh, row_strip):
        sr1 = min(sh, sr0 + row_strip)
        em_s = eval_mask_sub[sr0:sr1]
        if not em_s.any():
            continue
        gr0, gr1 = r0 + sr0, r0 + sr1
        b_blk = np.nan_to_num(base_mm[gr0:gr1, c0:c1, :], nan=0.0).astype(np.float32)
        u_blk = np.nan_to_num(udsr_mm[gr0:gr1, c0:c1, :], nan=0.0).astype(np.float32)
        s_blk = np.nan_to_num(sarpu_mm[gr0:gr1, c0:c1, :], nan=0.0).astype(np.float32)
        l_blk = lefm_sub[sr0:sr1]
        udsr._drop_mm_cache(base_mm)
        udsr._drop_mm_cache(udsr_mm)
        udsr._drop_mm_cache(sarpu_mm)

        lid_s = lid_sub[sr0:sr1]
        m_l = em_s & lid_s
        if m_l.any():
            X65_l = np.hstack([b_blk[m_l], u_blk[m_l], s_blk[m_l]])
            X67_l = np.hstack([X65_l, l_blk[m_l]])
            p_pure[sr0:sr1][m_l] = models["pure_full"].predict_proba_1(X65_l)
            p_coup[sr0:sr1][m_l] = models["coup_full"].predict_proba_1(X67_l)
            del X65_l, X67_l

        m_g = em_s & ~lid_s
        if m_g.any():
            X65_g = np.hstack([b_blk[m_g], u_blk[m_g], s_blk[m_g]])
            X67_g = np.hstack([X65_g, l_blk[m_g]])
            raw_p = models["pure_gap"].predict_proba_1(X65_g[:, NON_LIDAR_COLS_65])
            raw_c = models["coup_gap"].predict_proba_1(X67_g[:, NON_LIDAR_COLS_67])
            p_pure[sr0:sr1][m_g] = np.interp(raw_p, q_pure[0], q_pure[1]).astype(np.float32)
            p_coup[sr0:sr1][m_g] = np.interp(raw_c, q_coup[0], q_coup[1]).astype(np.float32)
            del X65_g, X67_g

    return p_pure, p_coup


def build_sarpu_surfaces(
    p_pure: np.ndarray,
    p_coupled: np.ndarray,
    blind_index: np.ndarray,
    active_mask: np.ndarray,
    d_vis: np.ndarray,
    flat_deep_playa: np.ndarray,
    d_collar: float = 15.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build bounded [0, 1] pre-placement continuous surfaces for EXP-1, EXP-2, and EXP-3.

    Returns ``(u_pure, u_coupled, u_tworegime_continuous)``, all strictly inside ``[0, 1]`` and
    zero outside ``active_mask & ~flat_deep_playa & (d_vis > 2.0)``.
    """
    valid = active_mask & (~flat_deep_playa) & (d_vis > 2.0)
    b_idx = np.clip(np.nan_to_num(blind_index, nan=0.0), 0.0, 1.0).astype(np.float32)

    raw_pure = np.where(
        valid,
        (np.clip(p_pure, 0.0, 1.0) ** 0.82) * (0.68 + 0.32 * b_idx),
        0.0,
    ).astype(np.float32)
    u_pure = np.clip(udsr.oriented_nms_4az(raw_pure, valid, blend=0.42), 0.0, 1.0)
    u_pure[~valid] = 0.0

    raw_coup = np.where(
        valid,
        (np.clip(p_coupled, 0.0, 1.0) ** 0.85) * (0.78 + 0.22 * b_idx),
        0.0,
    ).astype(np.float32)
    u_coup = np.clip(udsr.oriented_nms_4az(raw_coup, valid, blend=0.38), 0.0, 1.0)
    u_coup[~valid] = 0.0

    # Continuous pre-placement surface for EXP-3: rank-calibrated within each regime so collar (42%)
    # and far-basin (58%) have matched top-tail density prior to discrete submodular placement.
    u_two = np.zeros_like(u_pure)
    m_col = valid & (d_vis <= d_collar)
    m_far = valid & (d_vis > d_collar)
    if m_col.any():
        u_two[m_col] = udsr.rank01(u_coup, m_col)[m_col]
    if m_far.any():
        u_two[m_far] = udsr.rank01(u_pure, m_far)[m_far]
    return u_pure, u_coup, u_two


def _greedy_nms_stage(
    score: np.ndarray,
    eligible: np.ndarray,
    blocked: np.ndarray,
    budget: int,
    dy_off: np.ndarray,
    dx_off: np.ndarray,
    max_candidates: int = 360000,
) -> tuple[np.ndarray, int]:
    """Place up to ``budget`` binary dots from ``score`` inside ``eligible``, updating ``blocked`` in-place."""
    h, w = score.shape
    out = np.zeros((h, w), dtype=np.float32)
    if budget <= 0 or not eligible.any():
        return out, 0

    ys, xs = np.nonzero(eligible & (~blocked) & (score > 0.0))
    if ys.size == 0:
        return out, 0
    vals = score[ys, xs]
    if vals.size > max_candidates:
        part = np.argpartition(vals, vals.size - max_candidates)[vals.size - max_candidates :]
        ys, xs, vals = ys[part], xs[part], vals[part]
    # Deterministic tie-breaking: sort by (-val, y, x)
    order = np.lexsort((xs, ys, -vals))
    ys, xs = ys[order], xs[order]

    placed = 0
    for r, c in zip(ys.tolist(), xs.tolist()):
        if blocked[r, c]:
            continue
        out[r, c] = 1.0
        placed += 1
        rr = r + dy_off
        cc = c + dx_off
        ok = (rr >= 0) & (rr < h) & (cc >= 0) & (cc < w)
        blocked[rr[ok], cc[ok]] = True
        if placed >= budget:
            break
    return out, placed


def emit_two_regime_dots(
    u_collar: np.ndarray,
    u_far: np.ndarray,
    active_mask: np.ndarray,
    d_vis: np.ndarray,
    flat_deep_playa: np.ndarray,
    k_dots: int = 37654,
    collar_frac: float = 0.42,
    d_collar: float = 15.0,
    min_fault_dist_px: float = 2.0,
    min_sep_px: float = 2.85,
) -> tuple[np.ndarray, dict[str, int]]:
    """Two-stage collar-capped + far-basin submodular binary emitter with shared 2.85-px exclusion."""
    h, w = u_collar.shape
    valid = active_mask & (~flat_deep_playa) & (d_vis > float(min_fault_dist_px))
    blocked = ~valid

    rad = int(np.ceil(min_sep_px))
    yy, xx = np.mgrid[-rad : rad + 1, -rad : rad + 1]
    disk = (yy * yy + xx * xx) <= (min_sep_px * min_sep_px + 1e-6)
    dy_off, dx_off = yy[disk], xx[disk]

    k_col_cap = int(round(float(collar_frac) * int(k_dots)))
    m_col = valid & (d_vis <= float(d_collar))
    m_far = valid & (d_vis > float(d_collar))

    dots_col, n_col = _greedy_nms_stage(u_collar, m_col, blocked, k_col_cap, dy_off, dx_off)
    k_far_rem = max(0, int(k_dots) - n_col)
    dots_far, n_far = _greedy_nms_stage(u_far, m_far, blocked, k_far_rem, dy_off, dx_off)

    # If far-basin hits packing capacity on a tiny holdout crop, leave unused rather than violating collar cap
    out = np.clip(dots_col + dots_far, 0.0, 1.0).astype(np.float32)
    stats = {
        "n_total": int(n_col + n_far),
        "n_collar": int(n_col),
        "n_far": int(n_far),
        "collar_cap": int(k_col_cap),
    }
    return out, stats

