"""H-UDSR: Updip-Migrated Tilt-Depth & Transtensional Hydrothermal Fault-Trace Inversion.

Single frozen hypothesis lane pre-registered in ``knowledge/preregistration_udsr_20261027.md``.
Engineered for strict < 1.2 GiB peak RSS on 3.8 GiB zero-swap containers via staged band loading,
512-row strip advection, and sequential memmap access.
"""
from __future__ import annotations

import csv
import gc
import io
import json
import mmap
import struct
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from numpy.lib.format import open_memmap
from rasterio.warp import transform as warp_transform
from scipy.ndimage import (
    distance_transform_edt,
    gaussian_filter,
    gaussian_laplace,
    label,
    map_coordinates,
    maximum_filter,
    minimum_filter,
    zoom,
)
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from . import features

UDSR_CHANNELS: tuple[str, ...] = (
    # 0..14: strictly 1 m LiDAR-free (15 channels)
    "udsr_grav_tilt_ridge",        # 0: Miller-Singh / Salem gravity tilt contact ridge
    "udsr_rtp_tilt_ridge",         # 1: Miller-Singh / Salem RTP magnetic tilt contact ridge
    "udsr_updip_grav_trace",       # 2: Footwall updip-advected gravity contact onto surface break
    "udsr_updip_rtp_demag",        # 3: Footwall updip-advected RTP contact + magnetite-loss trough
    "udsr_updip_mt_conduit",       # 4: Footwall updip-advected MT conductance (Band 17) conduit
    "udsr_gallardo_coupling",      # 5: Gallardo-Meju (2003) gravity-magnetic structural coupling
    "udsr_transtension_potency",   # 6: Geodetic dilation x shear x 2nd-invariant potency
    "udsr_morris_slip_align",      # 7: Morris slip-dilation NNE-NE strike alignment of PF tensor
    "udsr_seis_basement_step",     # 8: Declustered + induced microseismicity x basement step
    "udsr_piedmont_locus",         # 9: Piedmont / horst-margin depth-relief locus (playa-vetoed)
    "udsr_sio2_geotherm_plume",    # 10: DOE GDR #1391 quartz/chalcedony/cation geothermometer plume
    "udsr_probe2m_sinter_plume",   # 11: Sanitized 2m probe + paleo-sinter/travertine + vents plume
    "udsr_blk_potassic_ridge",     # 12: 4-block standardized GeoDAWN K-Th adularia ridge (road-clean)
    "udsr_blk_radon_ridge",        # 13: 4-block standardized GeoDAWN 214Bi (U-Th) radon ridge
    "udsr_unsup_updip_crest",      # 14: Unified label-free updip multi-physics 4-azimuth crest [0,1]
    # 15..17: 1 m LiDAR-assisted inside lidar_valid >= 128 (3 channels)
    "udsr_lidar_scarp_deconf",     # 15: Road- & shoreline-deconfounded 1m LiDAR step x coherence
    "udsr_lidar_aniso_1km",        # 16: 1 km anisotropic along-strike continuity of 1m LiDAR scarp
    "udsr_lidar_updip_bridge",     # 17: Concordance of 1m LiDAR scarp with updip PF/basement trace
)

VIS_CHANNELS: tuple[str, ...] = (
    "vis_tip_cone",                # Azimuthal PCA fault-tip propagation cone (visible-only)
    "vis_relay_bridge",            # Exact bit-partition 2nd-component stepover relay bridge (visible-only)
)

LIDAR_COLS_53: frozenset[int] = frozenset({50, 51, 52})
NON_LIDAR_COLS_53: tuple[int, ...] = tuple(i for i in range(53) if i not in LIDAR_COLS_53)


def _drop_mm_cache(mm_arr: np.ndarray) -> None:
    """Release clean memmap pages so cgroup file cache stays tiny on zero-swap containers."""
    base = getattr(mm_arr, "base", None)
    if isinstance(base, mmap.mmap) and hasattr(mmap, "MADV_DONTNEED"):
        try:
            base.madvise(mmap.MADV_DONTNEED)
        except Exception:
            pass


def robust_z(arr: np.ndarray, foot: np.ndarray, clip: float = 6.0) -> np.ndarray:
    sub = arr[foot][::8]
    sub = sub[np.isfinite(sub)]
    if sub.size == 0:
        return np.zeros(arr.shape, dtype=np.float32)
    q25, q50, q75 = np.percentile(sub, [25.0, 50.0, 75.0])
    scale = float(0.7413 * (q75 - q25))
    if scale < 1e-6:
        scale = float(np.std(sub)) + 1e-6
    out = np.nan_to_num(arr, nan=float(q50)).astype(np.float32, copy=True)
    out -= np.float32(q50)
    out /= np.float32(scale)
    np.clip(out, -clip, clip, out=out)
    out[~foot] = 0.0
    return out


def sigmoid_f32(x: np.ndarray) -> np.ndarray:
    y = np.clip(x, -12.0, 12.0).astype(np.float32, copy=False)
    return (1.0 / (1.0 + np.exp(-y))).astype(np.float32)


def rank01(arr: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Fast memory-lean quantile-interpolated rank in [0, 1] inside footprint (~50 MB peak vs 200 MB argsort)."""
    sub = np.nan_to_num(arr[foot][::4], nan=0.0).astype(np.float32)
    qs = np.linspace(0.0, 100.0, 513)
    knots = np.percentile(sub, qs).astype(np.float32)
    # Enforce tiny strict monotonicity for flat ties
    knots += np.linspace(0.0, 1e-7, knots.size, dtype=np.float32)
    probs = np.linspace(0.0, 1.0, knots.size, dtype=np.float32)
    out = np.zeros(arr.shape, dtype=np.float32)
    out[foot] = np.interp(np.nan_to_num(arr[foot], nan=0.0), knots, probs).astype(np.float32)
    return out


def load_band_clean(path: Path, foot: np.ndarray) -> np.ndarray:
    raw = np.load(path)
    valid = foot & np.isfinite(raw)
    med = float(np.median(raw[valid][::8])) if valid.any() else 0.0
    out = np.where(valid, raw, med).astype(np.float32)
    # Smooth any tiny interior missing islands seamlessly without 300 MB int64 EDT index tensor
    bad = foot & ~np.isfinite(raw)
    if bad.any():
        sm = gaussian_filter(out, sigma=3.0, mode="nearest")
        out[bad] = sm[bad]
    del raw
    return out


def advect_updip_field(
    source: np.ndarray,
    dy_downdip: np.ndarray,
    dx_downdip: np.ndarray,
    foot: np.ndarray,
    offsets_px: tuple[float, ...] = (2.5, 5.0, 8.0),
    weights: tuple[float, ...] = (0.45, 0.35, 0.20),
    dip_gate: np.ndarray | None = None,
    strip_rows: int = 512,
) -> np.ndarray:
    """Project hanging-wall subsurface ``source`` energy up-dip onto the footwall surface break.

    Processes in ``strip_rows`` bands (~13 MB temporary coords) while sampling from the full
    ``source`` array so strip boundaries are 100% exact (bit-identical to full-frame evaluation).
    """
    h, w = source.shape
    src_f = np.where(foot & np.isfinite(source), source, 0.0).astype(np.float32)
    acc = np.zeros((h, w), dtype=np.float32)
    xs_row = np.arange(w, dtype=np.float32)[None, :]

    for r0 in range(0, h, strip_rows):
        r1 = min(h, r0 + strip_rows)
        sh = r1 - r0
        ys_col = np.arange(r0, r1, dtype=np.float32)[:, None]
        dy_s = dy_downdip[r0:r1]
        dx_s = dx_downdip[r0:r1]
        coords = np.empty((2, sh, w), dtype=np.float32)
        acc_s = acc[r0:r1]
        for delta, wt in zip(offsets_px, weights):
            coords[0] = np.clip(ys_col + float(delta) * dy_s, 0.0, float(h - 1))
            coords[1] = np.clip(xs_row + float(delta) * dx_s, 0.0, float(w - 1))
            sampled = map_coordinates(src_f, coords, order=1, mode="nearest")
            acc_s += np.float32(wt) * np.maximum(sampled, 0.0)

    if dip_gate is not None:
        acc *= dip_gate.astype(np.float32, copy=False)
    acc[~foot] = 0.0
    return acc


def is_crest_4az(surface: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Boolean mask of 1-px cross-strike local ridge maxima across 4 strike orientations."""
    s = np.where(foot & np.isfinite(surface), np.maximum(surface, 0.0), 0.0).astype(np.float32)
    p = np.pad(s, 2, mode="edge")
    h, w = s.shape
    c = p[2 : h + 2, 2 : w + 2]
    m_ew = (c >= p[2 : h + 2, 1 : w + 1]) & (c >= p[2 : h + 2, 3 : w + 3]) & (
        c > 0.5 * (p[2 : h + 2, 0:w] + p[2 : h + 2, 4 : w + 4])
    )
    m_ns = (c >= p[1 : h + 1, 2 : w + 2]) & (c >= p[3 : h + 3, 2 : w + 2]) & (
        c > 0.5 * (p[0:h, 2 : w + 2] + p[4 : h + 4, 2 : w + 2])
    )
    m_nwse = (c >= p[1 : h + 1, 1 : w + 1]) & (c >= p[3 : h + 3, 3 : w + 3]) & (
        c > 0.5 * (p[0:h, 0:w] + p[4 : h + 4, 4 : w + 4])
    )
    m_nesw = (c >= p[1 : h + 1, 3 : w + 3]) & (c >= p[3 : h + 3, 1 : w + 1]) & (
        c > 0.5 * (p[0:h, 4 : w + 4] + p[4 : h + 4, 0:w])
    )
    return (m_ew | m_ns | m_nwse | m_nesw) & foot & (s > 0.0)


def oriented_nms_4az(surface: np.ndarray, foot: np.ndarray, blend: float = 0.45) -> np.ndarray:
    """Probability-rank-preserving 4-azimuth (0, 45, 90, 135 deg) axial crest sharpener."""
    s = np.where(foot & np.isfinite(surface), np.maximum(surface, 0.0), 0.0).astype(np.float32)
    crest = is_crest_4az(s, foot).astype(np.float32)
    out = ((1.0 - blend) * s + blend * s * crest) * foot.astype(np.float32)
    return out.astype(np.float32)


def exact_second_component_edt(comp_labels: np.ndarray, downsample: int = 2) -> np.ndarray:
    """Exact (up to optional grid stride) Euclidean distance to the 2nd-nearest DISTINCT component."""
    h, w = comp_labels.shape
    sub = comp_labels[::downsample, ::downsample] if downsample > 1 else comp_labels
    max_id = int(sub.max())
    if max_id <= 1:
        return np.full((h, w), 999.0, dtype=np.float32)
    n_bits = int(max_id).bit_length()
    d2_sub = np.full(sub.shape, 999.0, dtype=np.float32)
    pos = sub > 0
    for b in range(n_bits):
        bit_one = pos & (((sub >> b) & 1) == 1)
        bit_zero = pos & (((sub >> b) & 1) == 0)
        if not bit_one.any() or not bit_zero.any():
            continue
        e1 = distance_transform_edt(~bit_one).astype(np.float32) * float(downsample)
        e0 = distance_transform_edt(~bit_zero).astype(np.float32) * float(downsample)
        np.minimum(d2_sub, np.maximum(e0, e1), out=d2_sub)
    if downsample > 1:
        out = zoom(d2_sub, (h / d2_sub.shape[0], w / d2_sub.shape[1]), order=1).astype(np.float32)
        return out[:h, :w]
    return d2_sub


def compute_visible_continuation(visible_mask: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Derive 2 bounded [0, 1] structural continuation channels STRICTLY from ``visible_mask``."""
    vis = np.asarray(visible_mask, bool) & foot
    h, w = foot.shape
    out = np.zeros((h, w, 2), dtype=np.float32)
    if not vis.any():
        return out

    p = np.pad(vis.astype(np.int16), 1, mode="constant")
    nbr8 = (
        p[0:h, 0:w] + p[0:h, 1 : w + 1] + p[0:h, 2 : w + 2]
        + p[1 : h + 1, 0:w] + p[1 : h + 1, 2 : w + 2]
        + p[2 : h + 2, 0:w] + p[2 : h + 2, 1 : w + 1] + p[2 : h + 2, 2 : w + 2]
    )
    del p
    tips = vis & (nbr8 >= 1) & (nbr8 <= 2)
    del nbr8
    ty, tx = np.nonzero(tips)
    tip_field = np.zeros((h, w), dtype=np.float32)
    for y0, x0 in zip(ty, tx):
        r0, r1 = max(0, int(y0) - 5), min(h, int(y0) + 6)
        c0, c1 = max(0, int(x0) - 5), min(w, int(x0) + 6)
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
            ang = 0.5 * np.arctan2(2.0 * cov_yx, cov_xx - cov_yy + 1e-6)
            dirs = ((float(np.sin(ang)), float(np.cos(ang))), (-float(np.sin(ang)), -float(np.cos(ang))))
        else:
            dirs = ((-cy / nrm, -cx / nrm),)
        for duy, dux in dirs:
            for step in range(2, 16):
                py = int(round(float(y0) + step * duy))
                px = int(round(float(x0) + step * dux))
                if 0 <= py < h and 0 <= px < w:
                    val = float(np.exp(-step / 8.5))
                    if val > tip_field[py, px]:
                        tip_field[py, px] = val
    tip_cone = gaussian_filter(tip_field, sigma=1.6, mode="constant")
    del tip_field
    scale_t = float(np.percentile(tip_cone[foot][::4], 99.5)) + 1e-6
    out[:, :, 0] = np.where(foot, np.clip(tip_cone / scale_t, 0.0, 1.0), 0.0)
    del tip_cone

    comp, _ = label(vis, structure=np.ones((3, 3), dtype=int))
    # Compute d1 at downsample=2 as well to avoid 98 MB float64 full-res EDT allocation
    d1_sub = distance_transform_edt(~vis[::2, ::2]).astype(np.float32) * 2.0
    d1 = zoom(d1_sub, (h / d1_sub.shape[0], w / d1_sub.shape[1]), order=1).astype(np.float32)[:h, :w]
    d2 = exact_second_component_edt(comp, downsample=2)
    del comp, d1_sub
    relay = np.exp(-d1 / 9.0) * np.exp(-d2 / 11.0)
    scale_r = float(np.percentile(relay[foot][::4], 99.5)) + 1e-6
    out[:, :, 1] = np.where(foot, np.clip(relay / scale_r, 0.0, 1.0), 0.0)
    return out


def _rasterize_external_hydrothermal(ddir: Path, foot: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    ext = ddir / "external"
    h, w = foot.shape

    geotherm_grid = np.zeros((h, w), dtype=np.float32)
    n_geotherm_pts = 0
    with (ext / "gdr_wellspring_in_footprint.csv").open(encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            try:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
            except Exception:
                continue
            if not (0 <= r < h and 0 <= c < w and foot[r, c]):
                continue
            temps = []
            for k in ("temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c"):
                val_s = row.get(k, "")
                if val_s:
                    try:
                        v = float(val_s)
                        if 0.0 <= v <= 350.0:
                            temps.append(v)
                    except Exception:
                        pass
            if temps:
                excess = max(0.0, max(temps) - 25.0)
                if excess > 5.0:
                    n_geotherm_pts += 1
                    w_val = float(np.log1p(excess))
                    if w_val > geotherm_grid[r, c]:
                        geotherm_grid[r, c] = w_val

    plume_sio2 = (
        0.60 * gaussian_filter(geotherm_grid, sigma=3.5, mode="constant")
        + 0.40 * gaussian_filter(geotherm_grid, sigma=10.0, mode="constant")
    ).astype(np.float32)
    del geotherm_grid

    probe_grid = np.zeros((h, w), dtype=np.float32)
    n_f2m_overflow = 0
    n_probe_pts = 0
    with zipfile.ZipFile(ext / "2m_temperature_probe_INGENIOUS_regional_data.zip") as zf:
        raw = zf.read(
            "2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf"
        )
    numrec, lenhdr, reclen = struct.unpack("<4xIHH20x", raw[:32])
    fields = []
    pos = 32
    while raw[pos] != 0x0D and pos < lenhdr:
        fname = raw[pos : pos + 11].split(b"\x00", 1)[0].decode("ascii", "ignore")
        fields.append((fname, raw[pos + 16]))
        pos += 32

    recs_parsed = []
    area_t2m: dict[str, list[float]] = {}
    for i in range(numrec):
        rec = raw[lenhdr + 1 + i * reclen : lenhdr + 1 + (i + 1) * reclen]
        if not rec or rec[0:1] == b"*":
            continue
        cur = 1
        d = {}
        for fn, fl in fields:
            d[fn] = rec[cur : cur + fl].decode("utf-8", "ignore").strip()
            cur += fl
        try:
            lon = float(d["LongDegree"])
            lat = float(d["LatDegreeN"])
            t2m = float(d["T2m"])
        except Exception:
            continue
        f2m_val = None
        if d.get("F2mDAB"):
            try:
                fv = float(d["F2mDAB"])
                if abs(fv) > 50.0:
                    n_f2m_overflow += 1
                else:
                    f2m_val = fv
            except Exception:
                pass
        area = d.get("Area", "UNK")
        if 0.0 < t2m < 100.0:
            area_t2m.setdefault(area, []).append(t2m)
            recs_parsed.append((lon, lat, t2m, f2m_val, area))

    area_med = {a: float(np.median(vs)) for a, vs in area_t2m.items() if vs}
    if recs_parsed:
        pxs, pys = warp_transform(
            "EPSG:4269", "EPSG:32611", [r[0] for r in recs_parsed], [r[1] for r in recs_parsed]
        )
        for (_, _, t2m, f2m_val, area), ux, uy in zip(recs_parsed, pxs, pys):
            c = int(np.floor((ux - 243350.0) / 100.0))
            r = int(np.floor((4508550.0 - uy) / 100.0))
            if 0 <= r < h and 0 <= c < w and foot[r, c]:
                anom = f2m_val if f2m_val is not None else (t2m - area_med.get(area, 17.0))
                if anom > 1.0:
                    n_probe_pts += 1
                    v = float(np.log1p(anom))
                    if v > probe_grid[r, c]:
                        probe_grid[r, c] = v

    n_paleo_pts = 0
    with zipfile.ZipFile(ext / "paleo_geothermal_regional.zip") as zf:
        with io.TextIOWrapper(zf.open("Paleo_geothermal_final.csv"), encoding="utf-8", errors="replace") as f:
            p_lons, p_lats, p_wt = [], [], []
            for row in csv.DictReader(f):
                try:
                    lon = float(row["Long_deg_NAD83"])
                    lat = float(row["Lat_deg_NAD83"])
                    dtype = (row.get("Deposit_type") or "").lower()
                    wt = 2.5 if ("sinter" in dtype or "travertine" in dtype or "tufa" in dtype) else 1.8
                    p_lons.append(lon)
                    p_lats.append(lat)
                    p_wt.append(wt)
                except Exception:
                    pass
    if p_lons:
        uxs, uys = warp_transform("EPSG:4269", "EPSG:32611", p_lons, p_lats)
        for ux, uy, wt in zip(uxs, uys, p_wt):
            c = int(np.floor((ux - 243350.0) / 100.0))
            r = int(np.floor((4508550.0 - uy) / 100.0))
            if 0 <= r < h and 0 <= c < w and foot[r, c]:
                n_paleo_pts += 1
                probe_grid[r, c] = max(probe_grid[r, c], float(wt))

    n_vents = 0
    with (ext / "gdr_volcanic_vents_in_footprint.csv").open(encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            try:
                r, c = int(float(row["row"])), int(float(row["col"]))
                if 0 <= r < h and 0 <= c < w and foot[r, c]:
                    n_vents += 1
                    probe_grid[r, c] = max(probe_grid[r, c], 2.0)
            except Exception:
                pass

    plume_probe_sinter = (
        0.60 * gaussian_filter(probe_grid, sigma=3.0, mode="constant")
        + 0.40 * gaussian_filter(probe_grid, sigma=9.0, mode="constant")
    ).astype(np.float32)
    del probe_grid

    stats = {
        "geotherm_anomaly_points": n_geotherm_pts,
        "probe2m_positive_points": n_probe_pts,
        "f2mdab_overflow_records_sanitized": n_f2m_overflow,
        "paleo_sinter_travertine_in_footprint": n_paleo_pts,
        "volcanic_vents_in_footprint": n_vents,
    }
    return plume_sio2, plume_probe_sinter, stats


def _block_residual_ridge(
    num_u8: np.ndarray,
    den_u8: np.ndarray,
    blk_id: np.ndarray,
    foot: np.ndarray,
    road_gate: np.ndarray,
    playa_gate: np.ndarray,
) -> np.ndarray:
    resid = np.zeros(num_u8.shape, dtype=np.float32)
    nf = num_u8.astype(np.float32)
    df = den_u8.astype(np.float32)
    for b in np.unique(blk_id[foot]):
        m = foot & (blk_id == b) & (nf > 0) & (df > 0)
        if m.sum() < 200:
            continue
        x = df[m]
        y = nf[m]
        xm, ym = float(x.mean()), float(y.mean())
        beta = float(np.dot(x - xm, y - ym) / (np.dot(x - xm, x - xm) + 1e-6))
        r = y - (ym + beta * (x - xm))
        q25, q50, q75 = np.percentile(r[::4], [25.0, 50.0, 75.0])
        sc = float(0.7413 * (q75 - q25)) + 1e-5
        resid[m] = np.clip((r - float(q50)) / sc, -4.0, 5.0)
    del nf, df
    ridge = features._hessian_ridge(gaussian_filter(resid, sigma=1.2, mode="nearest"), sigma=1.8)
    del resid
    out = np.maximum(ridge, 0.0) * road_gate * playa_gate
    return robust_z(out, foot)


def build_udsr_stack(ddir: Path, wdir: Path, force: bool = False, log=print) -> dict[str, Any]:
    """Build or open the 18-channel label-free H-UDSR stack memmap with staged low-RSS execution."""
    out_path = wdir / "udsr_stack_18.npy"
    meta_path = wdir / "udsr_stack_18_meta.json"
    bands_dir = wdir / "bands"
    foot = np.load(bands_dir / "_footprint.npy")
    h, w = foot.shape

    ext = ddir / "external"
    with rasterio.open(ext / "lidar_scarp_features_u8.tif") as ds_lid:
        lid_valid = (ds_lid.read(12) >= 128) & foot

    z_base = load_band_clean(bands_dir / "15_depth_to_base_surf.npy", foot)
    slope = load_band_clean(bands_dir / "19_det_elev_slope.npy", foot)
    flat_deep_playa = foot & (z_base > 300.0) & (slope < 2.0)

    if out_path.exists() and meta_path.exists() and not force:
        meta = json.loads(meta_path.read_text())
        return {
            "path": out_path,
            "channels": UDSR_CHANNELS,
            "foot": foot,
            "lidar_valid": lid_valid,
            "flat_deep_playa": flat_deep_playa,
            "meta": meta,
        }

    log("[H-UDSR] Stage 1/4: Gravity + RTP Tilt-Depth & Updip Advection...")
    mm = open_memmap(out_path, mode="w+", dtype=np.float32, shape=(h, w, len(UDSR_CHANNELS)))

    playa_gate = np.where(
        foot,
        1.0 - 0.88 * sigmoid_f32((z_base - 320.0) / 90.0) * sigmoid_f32((1.8 - slope) / 0.45),
        0.0,
    ).astype(np.float32)
    dip_gate = (
        np.tanh(np.maximum(z_base, 0.0) / 300.0)
        * np.exp(-np.maximum(z_base - 1500.0, 0.0) / 1400.0)
        * playa_gate
    ).astype(np.float32)

    zb_sm = gaussian_filter(np.maximum(z_base, 0.0), sigma=3.0, mode="nearest")
    dy_z, dx_z = np.gradient(zb_sm)
    nz = np.hypot(dy_z, dx_z).astype(np.float32) + 1e-6
    del zb_sm

    grav = load_band_clean(bands_dir / "13_iso_grav_anom.npy", foot)
    grav_hg = load_band_clean(bands_dir / "18_iso_grav_anom_hg.npy", foot)
    grav_vg = load_band_clean(bands_dir / "11_iso_grav_anom_vg.npy", foot)

    g_sm = gaussian_filter(grav, sigma=3.0, mode="nearest")
    dy_g, dx_g = np.gradient(g_sm)
    ng = np.hypot(dy_g, dx_g).astype(np.float32) + 1e-6
    vy = 0.60 * (dy_z / nz) - 0.40 * (dy_g / ng)
    vx = 0.60 * (dx_z / nz) - 0.40 * (dx_g / ng)
    vn = np.hypot(vy, vx) + 1e-6
    dy_down = (vy / vn).astype(np.float32)
    dx_down = (vx / vn).astype(np.float32)
    del g_sm, dy_z, dx_z, dy_g, dx_g, ng, vy, vx, vn

    theta_g = np.arctan2(grav_vg, np.abs(grav_hg) + 1e-5).astype(np.float32)
    gy_tg, gx_tg = np.gradient(gaussian_filter(theta_g, sigma=1.0, mode="nearest"))
    grav_tilt_sharp = (np.hypot(gx_tg, gy_tg) * np.exp(-np.abs(theta_g) / 0.45)).astype(np.float32)
    mm[:, :, 0] = robust_z(grav_tilt_sharp, foot)
    del gy_tg, gx_tg, grav_vg

    grav_src = np.maximum(robust_z(grav_hg, foot), 0.0) * np.exp(-np.abs(theta_g) / 0.65)
    mm[:, :, 2] = robust_z(advect_updip_field(grav_src, dy_down, dx_down, foot, dip_gate=dip_gate), foot)
    del grav_src, theta_g, grav_hg

    gy_g1, gx_g1 = np.gradient(gaussian_filter(grav, sigma=1.5, mode="nearest"))
    mg1 = np.hypot(gx_g1, gy_g1).astype(np.float32) + 1e-6
    del grav

    rtp = load_band_clean(bands_dir / "02_rtp.npy", foot)
    tmi_hg = load_band_clean(bands_dir / "03_tmi_hg.npy", foot)
    tmi_vg = load_band_clean(bands_dir / "09_tmi_vg.npy", foot)

    theta_m = np.arctan2(tmi_vg, np.abs(tmi_hg) + 1e-5).astype(np.float32)
    gy_tm, gx_tm = np.gradient(gaussian_filter(theta_m, sigma=1.0, mode="nearest"))
    rtp_tilt_sharp = (np.hypot(gx_tm, gy_tm) * np.exp(-np.abs(theta_m) / 0.45)).astype(np.float32)
    mm[:, :, 1] = robust_z(rtp_tilt_sharp, foot)
    del gy_tm, gx_tm, tmi_vg

    rtp_demag = np.maximum(gaussian_laplace(rtp, sigma=2.0, mode="nearest"), 0.0)
    rtp_src = 0.60 * np.maximum(robust_z(tmi_hg, foot), 0.0) * np.exp(-np.abs(theta_m) / 0.65) + 0.40 * np.maximum(
        robust_z(rtp_demag, foot), 0.0
    )
    mm[:, :, 3] = robust_z(advect_updip_field(rtp_src, dy_down, dx_down, foot, dip_gate=dip_gate), foot)
    del rtp_demag, rtp_src, theta_m, tmi_hg

    gy_m1, gx_m1 = np.gradient(gaussian_filter(rtp, sigma=1.5, mode="nearest"))
    mm1 = np.hypot(gx_m1, gy_m1).astype(np.float32) + 1e-6
    del rtp
    cos_align = ((gx_g1 * gx_m1 + gy_g1 * gy_m1) / (mg1 * mm1)) ** 2
    mm[:, :, 5] = robust_z(np.sqrt(np.maximum(grav_tilt_sharp * rtp_tilt_sharp, 0.0)) * cos_align * playa_gate, foot)
    del grav_tilt_sharp, rtp_tilt_sharp, cos_align

    nx_opt, ny_opt = np.float32(0.9272), np.float32(0.3746)
    align_pf = (0.55 * ((gx_g1 * nx_opt + gy_g1 * ny_opt) / mg1) ** 2 + 0.45 * ((gx_m1 * nx_opt + gy_m1 * ny_opt) / mm1) ** 2).astype(np.float32)
    del gx_g1, gy_g1, gx_m1, gy_m1, mg1, mm1
    mm.flush()
    _drop_mm_cache(mm)
    gc.collect()

    log("[H-UDSR] Stage 2/4: MT Conductance, Transtension, Seismicity & Piedmont...")
    cond = load_band_clean(bands_dir / "17_cond_surf.npy", foot)
    cond_log = np.log1p(np.maximum(cond, 0.0))
    del cond
    cy_c, cx_c = np.gradient(gaussian_filter(cond_log, sigma=1.5, mode="nearest"))
    cond_src = 0.65 * np.maximum(robust_z(np.hypot(cx_c, cy_c), foot), 0.0) + 0.35 * np.maximum(
        robust_z(features._hessian_ridge(cond_log, 2.2), foot), 0.0
    )
    del cond_log, cy_c, cx_c
    mm[:, :, 4] = robust_z(advect_updip_field(cond_src, dy_down, dx_down, foot, dip_gate=dip_gate), foot)
    del cond_src, dy_down, dx_down, dip_gate

    geod_2nd = load_band_clean(bands_dir / "04_geod_2ndinv.npy", foot)
    geod_sh = load_band_clean(bands_dir / "07_geod_shearrate.npy", foot)
    geod_dil = load_band_clean(bands_dir / "08_geod_dilaterate.npy", foot)
    transtens = (
        sigmoid_f32(robust_z(geod_dil, foot))
        * sigmoid_f32(robust_z(geod_sh, foot))
        * sigmoid_f32(robust_z(geod_2nd, foot))
    )
    del geod_2nd, geod_sh, geod_dil
    mm[:, :, 6] = robust_z(transtens, foot)
    mm[:, :, 7] = robust_z(align_pf * sigmoid_f32(0.5 * mm[:, :, 2] + 0.5 * mm[:, :, 0]) * transtens, foot)
    del align_pf, transtens

    deq = load_band_clean(bands_dir / "10_deq_n100a15.npy", foot)
    ieq = load_band_clean(bands_dir / "16_ieq_n100a15.npy", foot)
    seis = (0.60 * np.maximum(robust_z(deq, foot), -1.0) + 0.40 * np.maximum(robust_z(ieq, foot), -1.0)) * np.maximum(
        robust_z(nz, foot), 0.0
    )
    del deq, ieq, nz
    mm[:, :, 8] = robust_z(seis, foot)
    del seis

    det_elev = load_band_clean(bands_dir / "12_det_elev.npy", foot)
    rel_2km = maximum_filter(det_elev, size=21) - minimum_filter(det_elev, size=21)
    depth_win = np.exp(-((np.log(np.maximum(z_base, 25.0) / 260.0)) ** 2) / 2.0).astype(np.float32)
    mm[:, :, 9] = robust_z(sigmoid_f32(robust_z(rel_2km, foot)) * depth_win * playa_gate, foot)
    del rel_2km, depth_win
    topo_ridge1 = features._hessian_ridge(det_elev, 1.2)
    del det_elev
    mm.flush()
    _drop_mm_cache(mm)
    gc.collect()

    log("[H-UDSR] Stage 3/4: Sanitized Hydrothermal Plumes & Block-Leveled GeoDAWN...")
    plume_sio2, plume_probe, hydro_stats = _rasterize_external_hydrothermal(ddir, foot)
    mm[:, :, 10] = robust_z(plume_sio2 * playa_gate, foot)
    mm[:, :, 11] = robust_z(plume_probe * playa_gate, foot)
    del plume_sio2, plume_probe

    with rasterio.open(ext / "tiger_road_distance_m.tif") as ds_rd:
        d_road = np.nan_to_num(ds_rd.read(1), nan=1000.0).astype(np.float32)
    road_gate = (1.0 - 0.75 * np.exp(-((d_road / 150.0) ** 2))).astype(np.float32)
    del d_road
    with rasterio.open(ext / "acquisition_block_id_100m.tif") as ds_blk:
        blk_id = ds_blk.read(1)
    with rasterio.open(ext / "geodawn_rad_u8.tif") as ds_rad:
        k_u8 = ds_rad.read(1)
        th_u8 = ds_rad.read(2)
        u_u8 = ds_rad.read(3)

    mm[:, :, 12] = _block_residual_ridge(k_u8, th_u8, blk_id, foot, road_gate, playa_gate)
    mm[:, :, 13] = _block_residual_ridge(u_u8, th_u8, blk_id, foot, road_gate, playa_gate)
    del k_u8, th_u8, u_u8, blk_id
    mm.flush()
    _drop_mm_cache(mm)
    gc.collect()

    log("[H-UDSR] Stage 4/4: De-confounded 1m LiDAR & Unified Updip Crest S_phys...")
    pf_support = sigmoid_f32(0.45 * mm[:, :, 2] + 0.35 * mm[:, :, 3] + 0.20 * mm[:, :, 0])
    shoreline_damp = np.where((z_base > 180.0) & (slope < 3.5) & (pf_support < 0.48), 0.35, 1.0).astype(np.float32)
    del pf_support

    with rasterio.open(ext / "lidar_scarp_features_u8.tif") as ds_lid:
        step_max = ds_lid.read(3).astype(np.float32) / 255.0
        relief_lid = ds_lid.read(9).astype(np.float32) / 255.0
        coh100 = ds_lid.read(10).astype(np.float32) / 255.0

    lid_clean = (
        (0.65 * step_max * (0.4 + 0.6 * coh100) + 0.35 * relief_lid * coh100)
        * road_gate
        * shoreline_damp
        * playa_gate
    )
    del step_max, relief_lid, coh100
    lid_clean = np.where(lid_valid, lid_clean, 0.0).astype(np.float32)
    mm[:, :, 15] = np.where(lid_valid, robust_z(lid_clean, lid_valid), 0.0)

    lid_sm = 0.6 * gaussian_filter(lid_clean, sigma=1.5, mode="constant") + 0.4 * gaussian_filter(
        lid_clean, sigma=4.5, mode="constant"
    )
    mm[:, :, 16] = np.where(lid_valid, robust_z(np.sqrt(np.maximum(lid_clean * lid_sm, 0.0)), lid_valid), 0.0)
    del lid_sm

    updip_combo = np.maximum(0.55 * sigmoid_f32(mm[:, :, 2]) + 0.45 * sigmoid_f32(mm[:, :, 3]), 0.0)
    mm[:, :, 17] = np.where(lid_valid, robust_z(np.sqrt(np.maximum(lid_clean * updip_combo, 0.0)), lid_valid), 0.0)
    del lid_clean, updip_combo

    topo_clean = robust_z(np.maximum(topo_ridge1, 0.0) * road_gate * shoreline_damp * playa_gate, foot)
    del topo_ridge1, road_gate, shoreline_damp
    raw_phys = (
        0.24 * rank01(mm[:, :, 2], foot)
        + 0.16 * rank01(mm[:, :, 3], foot)
        + 0.12 * rank01(mm[:, :, 4], foot)
        + 0.12 * rank01(mm[:, :, 0], foot)
        + 0.08 * rank01(mm[:, :, 5], foot)
        + 0.14 * rank01(topo_clean, foot)
        + 0.06 * rank01(mm[:, :, 9], foot)
        + 0.04 * rank01(0.5 * mm[:, :, 10] + 0.5 * mm[:, :, 11], foot)
        + 0.04 * rank01(0.5 * mm[:, :, 12] + 0.5 * mm[:, :, 13], foot)
    ) * playa_gate
    del topo_clean, playa_gate
    mm[:, :, 14] = oriented_nms_4az(rank01(raw_phys, foot), foot, blend=0.45)
    del raw_phys
    mm.flush()
    _drop_mm_cache(mm)
    del mm
    gc.collect()

    meta = {
        "n_channels": len(UDSR_CHANNELS),
        "channels": list(UDSR_CHANNELS),
        "lidar_valid_px": int(lid_valid.sum()),
        "lidar_gap_px": int((foot & ~lid_valid).sum()),
        "lidar_gap_fraction": round(float((foot & ~lid_valid).sum() / foot.sum()), 6),
        "flat_deep_playa_px": int(flat_deep_playa.sum()),
        "flat_deep_playa_fraction": round(float(flat_deep_playa.sum() / foot.sum()), 6),
        "hydrothermal_stats": hydro_stats,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    log(f"[H-UDSR] Saved {out_path.name} | LiDAR gap={meta['lidar_gap_fraction']*100:.2f}% | Hydro={hydro_stats}")
    return {
        "path": out_path,
        "channels": UDSR_CHANNELS,
        "foot": foot,
        "lidar_valid": lid_valid,
        "flat_deep_playa": flat_deep_playa,
        "meta": meta,
    }


def _extract_features_sorted(
    ys: np.ndarray,
    xs: np.ndarray,
    base_mm: np.ndarray,
    udsr_mm: np.ndarray,
    vis_cont: np.ndarray,
    batch: int = 25000,
) -> np.ndarray:
    """Sequential-friendly batched memmap gather + page-cache release."""
    n = ys.size
    out = np.empty((n, 55), dtype=np.float32)
    order = np.argsort(ys, kind="mergesort")
    ys_s, xs_s = ys[order], xs[order]
    tmp = np.empty((n, 55), dtype=np.float32)
    for s in range(0, n, batch):
        e = min(n, s + batch)
        yb, xb = ys_s[s:e], xs_s[s:e]
        tmp[s:e, 0:35] = np.nan_to_num(base_mm[yb, xb, :], nan=0.0)
        tmp[s:e, 35:53] = np.nan_to_num(udsr_mm[yb, xb, :], nan=0.0)
        tmp[s:e, 53:55] = vis_cont[yb, xb, :]
        _drop_mm_cache(base_mm)
        _drop_mm_cache(udsr_mm)
    out[order] = tmp
    return out


def run_leakage_canary(
    base_mm: np.ndarray,
    udsr_mm: np.ndarray,
    ctx: Any,
    max_auc_threshold: float = 0.90,
    seed: int = 20261027,
) -> dict[str, Any]:
    """Protocol Rule 4 Leakage Canary: test EVERY feature alone on the buffered holdout."""
    rng = np.random.default_rng(seed)
    pos_rows, neg_rows = [], []

    for cell in ctx.cells:
        sl = cell.bbox
        vis_cont_full = compute_visible_continuation(cell.visible_full, ctx.foot)
        act = cell.active_sub & (cell.d_vis_sub > 2.0)
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
        pos_rows.append(_extract_features_sorted(py + r0, px + c0, base_mm, udsr_mm, vis_cont_full))
        neg_rows.append(_extract_features_sorted(ny + r0, nx + c0, base_mm, udsr_mm, vis_cont_full))
        del vis_cont_full
        gc.collect()

    X_pos = np.vstack(pos_rows)
    X_neg = np.vstack(neg_rows)
    y = np.concatenate([np.ones(len(X_pos), dtype=np.int8), np.zeros(len(X_neg), dtype=np.int8)])
    X = np.vstack([X_pos, X_neg])

    all_names = list(features.CHANNELS) + list(UDSR_CHANNELS) + list(VIS_CHANNELS)
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


def _extract_phys53_sorted(
    ys: np.ndarray,
    xs: np.ndarray,
    base_mm: np.ndarray,
    udsr_mm: np.ndarray,
    batch: int = 25000,
) -> np.ndarray:
    """Sequential-friendly batched memmap gather of the 53 pure physical channels."""
    n = ys.size
    out = np.empty((n, 53), dtype=np.float32)
    order = np.argsort(ys, kind="mergesort")
    ys_s, xs_s = ys[order], xs[order]
    tmp = np.empty((n, 53), dtype=np.float32)
    for s in range(0, n, batch):
        e = min(n, s + batch)
        yb, xb = ys_s[s:e], xs_s[s:e]
        tmp[s:e, 0:35] = np.nan_to_num(base_mm[yb, xb, :], nan=0.0)
        tmp[s:e, 35:53] = np.nan_to_num(udsr_mm[yb, xb, :], nan=0.0)
        _drop_mm_cache(base_mm)
        _drop_mm_cache(udsr_mm)
    out[order] = tmp
    return out


def fit_dual_cover_models(
    train_domain: np.ndarray,
    visible_faults: np.ndarray,
    lidar_valid: np.ndarray,
    base_mm: np.ndarray,
    udsr_mm: np.ndarray,
    seed: int = 20261027,
) -> tuple[HistGradientBoostingClassifier, HistGradientBoostingClassifier, np.ndarray]:
    """Fit pure-physical M_Full (53 ch inside LiDAR) and M_Gap (50 LiDAR-free ch) in ``train_domain``.

    Orthogonal Bayes factorization: neither tree model ever sees catalogue distance or continuation
    features, forcing every split to learn geophysical/geomorphic/hydrothermal fault physics while
    preserving strong blind far-field discrimination (d > 15 px).
    """
    rng = np.random.default_rng(seed)
    h, w = visible_faults.shape
    d_sub = distance_transform_edt(~visible_faults[::2, ::2]).astype(np.float32) * 2.0
    d_vis = zoom(d_sub, (h / d_sub.shape[0], w / d_sub.shape[1]), order=1).astype(np.float32)[:h, :w]
    del d_sub

    pos_all = visible_faults & train_domain
    neg_all = train_domain & (d_vis > 4.0)

    # 1. Fit M_Gap on 50 strictly 1m-LiDAR-free physical channels across train_domain
    py_g, px_g = np.nonzero(pos_all)
    ny_g, nx_g = np.nonzero(neg_all)
    if py_g.size > 32000:
        i = rng.choice(py_g.size, 32000, replace=False)
        py_g, px_g = py_g[i], px_g[i]
    n_neg_g = min(ny_g.size, max(96000, 3 * py_g.size))
    in_g = rng.choice(ny_g.size, n_neg_g, replace=False)
    ny_g, nx_g = ny_g[in_g], nx_g[in_g]

    Xg_p = _extract_phys53_sorted(py_g, px_g, base_mm, udsr_mm)[:, NON_LIDAR_COLS_53]
    Xg_n = _extract_phys53_sorted(ny_g, nx_g, base_mm, udsr_mm)[:, NON_LIDAR_COLS_53]
    Xg = np.vstack([Xg_p, Xg_n])
    yg = np.concatenate([np.ones(len(Xg_p), dtype=np.int8), np.zeros(len(Xg_n), dtype=np.int8)])
    del Xg_p, Xg_n

    m_gap = HistGradientBoostingClassifier(
        max_iter=175,
        learning_rate=0.06,
        max_leaf_nodes=31,
        min_samples_leaf=80,
        l2_regularization=2.0,
        random_state=seed,
    )
    m_gap.fit(Xg, yg)
    del Xg, yg

    # 2. Fit M_Full on all 53 physical channels inside lidar_valid & train_domain
    py_f, px_f = np.nonzero(pos_all & lidar_valid)
    ny_f, nx_f = np.nonzero(neg_all & lidar_valid)
    if py_f.size > 32000:
        i = rng.choice(py_f.size, 32000, replace=False)
        py_f, px_f = py_f[i], px_f[i]
    n_neg_f = min(ny_f.size, max(96000, 3 * py_f.size))
    in_f = rng.choice(ny_f.size, n_neg_f, replace=False)
    ny_f, nx_f = ny_f[in_f], nx_f[in_f]

    Xf_p = _extract_phys53_sorted(py_f, px_f, base_mm, udsr_mm)
    Xf_n = _extract_phys53_sorted(ny_f, nx_f, base_mm, udsr_mm)
    Xf = np.vstack([Xf_p, Xf_n])
    yf = np.concatenate([np.ones(len(Xf_p), dtype=np.int8), np.zeros(len(Xf_n), dtype=np.int8)])
    del Xf_p, Xf_n

    m_full = HistGradientBoostingClassifier(
        max_iter=175,
        learning_rate=0.06,
        max_leaf_nodes=31,
        min_samples_leaf=80,
        l2_regularization=2.0,
        random_state=seed + 101,
    )
    m_full.fit(Xf, yf)
    del Xf, yf

    # Quantile calibration curve aligning M_Gap posterior onto M_Full distribution
    cal_y, cal_x = np.nonzero(train_domain & lidar_valid & (d_vis > 2.0))
    if cal_y.size > 24000:
        ic = rng.choice(cal_y.size, 24000, replace=False)
        cal_y, cal_x = cal_y[ic], cal_x[ic]
    X_cal = _extract_phys53_sorted(cal_y, cal_x, base_mm, udsr_mm)
    pf_cal = m_full.predict_proba(X_cal)[:, 1]
    pg_cal = m_gap.predict_proba(X_cal[:, NON_LIDAR_COLS_53])[:, 1]
    qs = np.linspace(0.0, 100.0, 201)
    q_table = np.vstack([np.percentile(pg_cal, qs), np.percentile(pf_cal, qs)]).astype(np.float32)

    del X_cal, d_vis
    gc.collect()
    return m_full, m_gap, q_table


def predict_dual_cover_bbox(
    bbox: tuple[slice, slice],
    eval_mask_sub: np.ndarray,
    lidar_valid: np.ndarray,
    base_mm: np.ndarray,
    udsr_mm: np.ndarray,
    m_full: HistGradientBoostingClassifier,
    m_gap: HistGradientBoostingClassifier,
    q_table: np.ndarray,
    row_strip: int = 256,
) -> np.ndarray:
    """Sequential strip-streaming pure-physical Dual-Cover posterior prediction."""
    r0 = int(bbox[0].start)
    c0, c1 = int(bbox[1].start), int(bbox[1].stop)
    sh, sw = eval_mask_sub.shape
    out = np.zeros((sh, sw), dtype=np.float32)
    lid_sub = lidar_valid[bbox]

    for sr0 in range(0, sh, row_strip):
        sr1 = min(sh, sr0 + row_strip)
        em_strip = eval_mask_sub[sr0:sr1]
        if not em_strip.any():
            continue
        gr0, gr1 = r0 + sr0, r0 + sr1
        b_blk = np.nan_to_num(base_mm[gr0:gr1, c0:c1, :], nan=0.0).astype(np.float32)
        u_blk = np.nan_to_num(udsr_mm[gr0:gr1, c0:c1, :], nan=0.0).astype(np.float32)
        _drop_mm_cache(base_mm)
        _drop_mm_cache(udsr_mm)

        lid_s = lid_sub[sr0:sr1]
        m_l = em_strip & lid_s
        if m_l.any():
            X_l = np.hstack([b_blk[m_l], u_blk[m_l]])
            out[sr0:sr1][m_l] = m_full.predict_proba(X_l)[:, 1].astype(np.float32)

        m_g = em_strip & ~lid_s
        if m_g.any():
            X_g = np.hstack([b_blk[m_g], u_blk[m_g]])[:, NON_LIDAR_COLS_53]
            raw_p = m_gap.predict_proba(X_g)[:, 1].astype(np.float32)
            out[sr0:sr1][m_g] = np.interp(raw_p, q_table[0], q_table[1]).astype(np.float32)

    return out
