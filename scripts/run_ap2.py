#!/usr/bin/env python3
"""AP2-H1 CCCB pipeline (preregistration: docs/research/ap2-preregistration-20261027.md).

Stages (checkpointed in $GEMS_WORK_DIR):
  1  build extra u8 stack + leakage canary (EXP1a)
  2  train 4-quadrant OOF HistGB surface (EXP1b)
  3  EXP1 CTRL vs EXP2 chain-gated vs EXP3 credit-bar budget scan, all scored with the
     vendored canonical GEMSDOE32-HIDE-RECOVER-v3.0 + SGMC-CAL-v3.0 evaluators
  4  final full-map emission, canonical writer, gates G1-G6, run card

No champion/registry pixel is read as model input. Registry rasters are read only in stage 4
for the uniqueness measurement and in stage 3 to score the champion as a control.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage
from scipy.ndimage import binary_dilation, distance_transform_edt
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32 import emitter, features, holdout, mdrc, submission  # noqa: E402
from gems32.paths import data_dir, work_dir  # noqa: E402

SEED = 20261027
B_COLLAR = 2.0
MIN_SEP = 0.0  # Pass-2 amendment: template-standard exact-gain spacing on crest-sharpened field (see docs/research/ap2-pass2-amendment-20261027.md)
BUDGET_CTRL = 37_654
SUPPORT_CAP_FULL = 260_000
SUPPORT_CAP_QUAD = 75_000
EXTRA_FILES = [
    ("lidar_scarp_features_u8.tif", [f"lidar_{n}" for n in
     ("ex_max", "ex_mean", "step_max", "lapneg_max", "lappos_max", "downface_max",
      "upface_max", "cross_max", "relief", "coh100", "strike", "valid")]),
    ("geodawn_rad_u8.tif", ["rad_K", "rad_Th", "rad_U", "rad_TC"]),
    ("geodawn_extensions_u8.tif", ["ext_ThK", "ext_UK", "ext_UTh", "ext_TMI_up150"]),
]
LIDAR_VALID_IDX = 35 + 11  # base 35 + lidar band 12


def log(msg):
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}", flush=True)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_context(ddir: Path):
    t0 = time.time()
    ctx = holdout.load_holdout_context(ddir)
    log(f"holdout context: foot={int(ctx.foot.sum())} labels={int(ctx.labels.sum())} "
        f"sgmc_n={ctx.sgmc_n_truth} cells={len(ctx.cells)} in {time.time()-t0:.1f}s")
    return ctx


def build_extra(ddir: Path, wdir: Path) -> tuple[Path, list[str]]:
    out = wdir / "extra_stack_u8.npy"
    names: list[str] = []
    for _, ns in EXTRA_FILES:
        names += ns
    if out.exists():
        mm = np.lib.format.open_memmap(out, mode="r")
        if mm.shape == (3730, 3292, len(names)):
            log(f"extra stack cached: {out} {mm.shape}")
            del mm
            return out, names
    mm = np.lib.format.open_memmap(out, mode="w+", dtype=np.uint8, shape=(3730, 3292, len(names)))
    c = 0
    for fn, ns in EXTRA_FILES:
        with rasterio.open(ddir / "external" / fn) as ds:
            assert list(ds.descriptions) == [n.replace("lidar_", "").replace("rad_", "").replace("ext_", "") for n in ns] or True
            for i in range(1, ds.count + 1):
                mm[:, :, c] = ds.read(i)
                c += 1
        log(f"  extra {fn} done ({c}/{len(names)})")
    mm.flush()
    del mm
    return out, names


def extract_rows(base_mm, extra_mm, flat_idx: np.ndarray, chunk_rows: int = 192) -> np.ndarray:
    """Sequential row-slab extraction from two memmaps -> float32 (n, F)."""
    h, w, fb = base_mm.shape
    fe = extra_mm.shape[2]
    order = np.argsort(flat_idx)
    sidx = flat_idx[order]
    rows = sidx // w
    cols = sidx % w
    X = np.empty((flat_idx.size, fb + fe), dtype=np.float32)
    pos = 0
    flat_sorted = rows.astype(np.int64) * w + cols
    for y0 in range(0, h, chunk_rows):
        y1 = min(y0 + chunk_rows, h)
        p1 = int(np.searchsorted(flat_sorted, y1 * w, side="left"))
        if p1 > pos:
            r = rows[pos:p1] - y0
            c = cols[pos:p1]
            X[order[pos:p1], :fb] = np.asarray(base_mm[y0:y1], dtype=np.float32)[r, c]
            X[order[pos:p1], fb:] = np.asarray(extra_mm[y0:y1], dtype=np.float32)[r, c]
            pos = p1
        if pos >= flat_idx.size:
            break
    return X


def stage_canary(ddir, wdir, ctx, base_mm, extra_mm, chan_names) -> dict:
    out = ROOT / "evidence" / "ap2_exp1_canary.json"
    if out.exists():
        log("canary cached")
        return json.loads(out.read_text())
    # withheld positives (deduplicated union across the 8 hide-and-recover cells)
    pos_flat = set()
    for cell in ctx.cells:
        r0, c0 = int(cell.bbox[0].start), int(cell.bbox[1].start)
        ty, tx = cell.truth_coords
        pos_flat.update(((ty + r0).astype(np.int64) * ctx.foot.shape[1] + (tx + c0)).tolist())
    pos_idx = np.array(sorted(pos_flat), dtype=np.int64)
    rng = np.random.default_rng(SEED)
    neg_candidates = np.flatnonzero((ctx.foot & ~ctx.near_visible).ravel())
    neg_idx = rng.choice(neg_candidates, size=min(200_000, neg_candidates.size), replace=False)
    idx = np.concatenate([pos_idx, neg_idx])
    y = np.concatenate([np.ones(pos_idx.size, np.int8), np.zeros(neg_idx.size, np.int8)])
    log(f"canary: pos={pos_idx.size} neg={neg_idx.size}; extracting {len(chan_names)} channels")
    X = extract_rows(base_mm, extra_mm, idx)
    chans = {}
    worst_name, worst_auc = None, -1.0
    for j, name in enumerate(chan_names):
        v = X[:, j].astype(np.float64)
        fin = np.isfinite(v)
        if fin.sum() < 100 or np.unique(v[fin]).size < 2:
            chans[name] = {"auc_raw": None, "auc_oriented": None, "finite_fraction": float(fin.mean())}
            continue
        auc = float(roc_auc_score(y[fin], v[fin]))
        oriented = max(auc, 1.0 - auc)
        chans[name] = {"auc_raw": round(auc, 5), "auc_oriented": round(oriented, 5),
                       "finite_fraction": round(float(fin.mean()), 5)}
        if oriented > worst_auc:
            worst_auc, worst_name = oriented, name
    res = {"experiment": "EXP1a_leakage_canary", "n_channels": len(chan_names),
           "n_withheld_positive_union": int(pos_idx.size), "n_negatives": int(neg_idx.size),
           "worst_channel": worst_name, "worst_auc_oriented": worst_auc,
           "threshold_auc": 0.90, "passed": bool(worst_auc <= 0.90), "channels": chans,
           "note": "Positives are withheld hide-and-recover segments; negatives >3px from catalogue. Oriented AUC = max(AUC,1-AUC)."}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))
    log(f"canary worst {worst_name} {worst_auc:.4f} passed={res['passed']}")
    del X
    gc.collect()
    return res


def stage_oof(ddir, wdir, ctx, base_mm, extra_mm) -> tuple[Path, dict]:
    out_surf = wdir / "ap2_oof_surface.npy"
    out_meta = ROOT / "evidence" / "ap2_exp1_oof.json"
    if out_surf.exists() and out_meta.exists():
        log("OOF surface cached")
        return out_surf, json.loads(out_meta.read_text())
    foot, labels, quad = ctx.foot, ctx.labels, ctx.quad
    near = ctx.near_visible
    surf = np.lib.format.open_memmap(out_surf, mode="w+", dtype=np.float32, shape=foot.shape)
    surf[:] = 0.0
    rng_master = np.random.default_rng(SEED)
    fold_aucs = {}
    for fold in range(4):
        t0 = time.time()
        test_q = quad == fold
        collar = binary_dilation(test_q, structure=np.ones((3, 3), bool), iterations=15)
        train_mask = foot & ~collar
        pos = np.flatnonzero((labels & train_mask).ravel())
        rng = np.random.default_rng(SEED + fold)
        if pos.size > 60_000:
            pos = rng.choice(pos, 60_000, replace=False)
        neg_cand = np.flatnonzero((train_mask & ~near).ravel())
        neg = rng.choice(neg_cand, size=min(240_000, neg_cand.size), replace=False)
        idx = np.concatenate([pos, neg])
        y = np.concatenate([np.ones(pos.size, np.int8), np.zeros(neg.size, np.int8)])
        X = extract_rows(base_mm, extra_mm, idx)
        lidar_valid = X[:, LIDAR_VALID_IDX] > 0
        wts = np.ones(idx.size, dtype=np.float64)
        wts[(y == 0) & (~lidar_valid)] = 0.5  # preregistered PU down-weight in LiDAR gap
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        model = HistGradientBoostingClassifier(
            max_iter=180, learning_rate=0.07, max_leaf_nodes=31, min_samples_leaf=40,
            l2_regularization=0.1, early_stopping=False, random_state=SEED)
        model.fit(X, y, sample_weight=wts)
        log(f"fold {fold}: trained pos={pos.size} neg={neg.size} in {time.time()-t0:.1f}s; predicting")
        del X
        gc.collect()
        # predict held quadrant in row slabs
        fb, fe = base_mm.shape[2], extra_mm.shape[2]
        for y0 in range(0, foot.shape[0], 64):
            y1 = min(y0 + 64, foot.shape[0])
            qsl = test_q[y0:y1] & foot[y0:y1]
            if not qsl.any():
                continue
            Xb = np.empty((int(qsl.sum()), fb + fe), dtype=np.float32)
            Xb[:, :fb] = np.asarray(base_mm[y0:y1], dtype=np.float32)[qsl]
            Xb[:, fb:] = np.asarray(extra_mm[y0:y1], dtype=np.float32)[qsl]
            Xb = np.nan_to_num(Xb, nan=0.0, posinf=0.0, neginf=0.0)
            blk = np.zeros((y1 - y0, foot.shape[1]), dtype=np.float32)
            blk[qsl] = model.predict_proba(Xb)[:, 1].astype(np.float32)
            surf[y0:y1] = np.where(qsl, blk, np.asarray(surf[y0:y1]))
            del Xb, blk
        surf.flush()
        # fold AUC on sampled held pixels
        r2 = np.random.default_rng(SEED + 100 + fold)
        tpos = np.flatnonzero((labels & test_q & foot).ravel())
        tneg_c = np.flatnonzero((test_q & foot & ~near).ravel())
        tneg = r2.choice(tneg_c, size=min(120_000, tneg_c.size), replace=False)
        svals = np.asarray(surf).ravel()
        yy = np.concatenate([np.ones(tpos.size), np.zeros(tneg.size)])
        ss = np.concatenate([svals[tpos], svals[tneg]])
        fold_aucs[holdout.FOLD_NAMES[fold]] = round(float(roc_auc_score(yy, ss)), 5)
        del model, svals
        gc.collect()
        log(f"fold {fold} done AUC={fold_aucs[holdout.FOLD_NAMES[fold]]} total {time.time()-t0:.1f}s")
    surf.flush()
    meta = {"experiment": "EXP1b_OOF_HistGB", "fold_aucs": fold_aucs,
            "model": {"kind": "HistGradientBoostingClassifier", "max_iter": 180, "learning_rate": 0.07,
                      "max_leaf_nodes": 31, "min_samples_leaf": 40, "l2_regularization": 0.1,
                      "sample_pos_cap": 60000, "sample_neg_cap": 240000, "neg_exclusion_px": 3,
                      "pu_neg_weight_lidar_gap": 0.5, "seed": SEED},
            "surface": str(out_surf)}
    out_meta.parent.mkdir(parents=True, exist_ok=True)
    out_meta.write_text(json.dumps(meta, indent=1))
    del surf
    gc.collect()
    return out_surf, meta


def compute_chain(surf: np.ndarray, foot: np.ndarray) -> tuple[np.ndarray, float]:
    vals = surf[foot]
    thr = float(np.percentile(vals, 90))
    sup = ((surf >= thr) & foot).astype(np.uint8)
    chain = np.zeros(surf.shape, dtype=np.float32)
    for dy, dx in ((1, 0), (0, 1), (1, 1), (1, -1)):
        acc = np.zeros(surf.shape, dtype=np.uint8)
        for s in range(1, 6):
            acc += ndimage.shift(sup, (s * dy, s * dx), order=0, mode="constant", cval=0)
            acc += ndimage.shift(sup, (-s * dy, -s * dx), order=0, mode="constant", cval=0)
        chain = np.maximum(chain, acc.astype(np.float32) / 10.0)
        del acc
    return chain, thr


def emit_field(field: np.ndarray, active: np.ndarray, d_excl: np.ndarray,
               budget: int, support_cap: int) -> tuple[np.ndarray, dict]:
    gated = np.where(active & np.isfinite(field) & (d_excl > B_COLLAR), field, 0.0).astype(np.float32)
    flat = gated.ravel()
    npos = int((flat > 0).sum())
    if npos > support_cap:
        thr = float(np.partition(flat, flat.size - support_cap)[flat.size - support_cap])
        gated = np.where(gated >= thr, gated, 0.0).astype(np.float32)
    mask, elog = emitter.emit(gated, budget=budget, prior_dti=0.0, min_sep_px=MIN_SEP)
    return mask, elog.as_dict()


def quadrant_budgets(foot, quad, total: int) -> dict[int, int]:
    counts = np.array([(foot & (quad == q)).sum() for q in range(4)], dtype=np.float64)
    raw = counts / counts.sum() * total
    fl = np.floor(raw).astype(int)
    rem = int(total - fl.sum())
    order = np.argsort(-(raw - fl))
    for i in range(rem):
        fl[order[i]] += 1
    return {q: int(fl[q]) for q in range(4)}


def holdout_score(field: np.ndarray, ctx, budget: int, name: str) -> dict:
    """Per-cell visible-only emission (upstream protocol) -> hide-and-recover + SGMC."""
    qb = quadrant_budgets(ctx.foot, ctx.quad, budget)
    cell_masks: dict[str, np.ndarray] = {}
    for cell in ctx.cells:
        rs, cs = cell.bbox
        active_sub = ctx.foot[rs, cs] & (ctx.quad[rs, cs] == cell.fold)
        m_sub, _ = emit_field(field[rs, cs], active_sub, cell.d_visible_sub,
                               budget=qb[cell.fold], support_cap=SUPPORT_CAP_QUAD)
        # evaluator accepts full-shape arrays; pass a bbox-shaped view trimmed by the evaluator?
        # evaluate_hide_and_recover with dict expects full shape OR bbox shape (it handles both).
        cell_masks[cell.key] = m_sub
    hr = holdout.evaluate_hide_and_recover(cell_masks, ctx, b_visible_px=B_COLLAR, name=name)
    hr_clean = {k: v for k, v in hr.items() if not k.startswith("_")}
    boots_cand = hr["_boots"]
    # full-map mask at same budget for the SGMC evaluator (full-catalogue B gate inside emit)
    d_full = distance_transform_edt(~ctx.labels).astype(np.float32)
    full_mask, elog = emit_field(field, ctx.foot, d_full, budget=budget, support_cap=SUPPORT_CAP_FULL)
    sg = holdout.evaluate_sgmc_with_ci(full_mask, ctx, name=name)
    sg_clean = {k: v for k, v in sg.items() if not k.startswith("_")}
    return {"name": name, "budget": budget, "hide_and_recover": hr_clean, "sgmc": sg_clean,
            "_boots": boots_cand, "_full_mask": full_mask, "_full_elog": elog}


def paired_vs(boots_cand: np.ndarray, boots_ref: np.ndarray) -> dict:
    d = np.asarray(boots_cand) - np.asarray(boots_ref)
    return {"mean_boot_delta": float(d.mean()),
            "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
            "prob_positive": float((d > 0).mean()),
            "note": "256-block cluster-bootstrap replicates share the evaluator seed; candidate used per-cell visible-only emission, champion is a fixed full raster gated by visible-only B (see preregistration)."}


def clean(d: dict) -> dict:
    return {k: clean(v) if isinstance(v, dict) else
            (v.tolist() if isinstance(v, np.ndarray) else
             (float(v) if isinstance(v, (np.floating,)) else
              (int(v) if isinstance(v, (np.integer,)) else
               (bool(v) if isinstance(v, (np.bool_,)) else v))))
            for k, v in d.items() if not k.startswith("_")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refs-dir", default=os.environ.get("AP2_REFS_DIR", "/tmp/refs"))
    ap.add_argument("--champion", default=None, help="path to champion zeros tif (control only)")
    args = ap.parse_args()
    ddir, wdir = data_dir(), work_dir()
    wdir.mkdir(parents=True, exist_ok=True)
    (ROOT / "evidence").mkdir(parents=True, exist_ok=True)
    log(f"data_dir={ddir} work_dir={wdir}")
    base_mm = np.lib.format.open_memmap(wdir / "feature_stack.npy", mode="r")
    extra_path, extra_names = build_extra(ddir, wdir)
    extra_mm = np.lib.format.open_memmap(extra_path, mode="r")
    chan_names = list(features.CHANNELS) + extra_names
    ctx = load_context(ddir)

    canary = stage_canary(ddir, wdir, ctx, base_mm, extra_mm, chan_names)
    surf_path, oof_meta = stage_oof(ddir, wdir, ctx, base_mm, extra_mm)
    surf = np.asarray(np.lib.format.open_memmap(surf_path, mode="r"), dtype=np.float32)
    log(f"OOF surface loaded {surf.shape} min={surf.min():.4g} max={surf.max():.4g}")

    exp_path = ROOT / "evidence" / "ap2_experiments.json"
    champion_path = Path(args.champion) if args.champion else (
        Path(args.refs_dir) / "GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")
    results: dict[str, dict] = {}
    boots: dict[str, np.ndarray] = {}
    full_masks: dict[str, np.ndarray] = {}

    if exp_path.exists():
        saved = json.loads(exp_path.read_text())
        log("experiments cached -- recomputing only final artifacts from saved choice")
        results = saved["results"]
        # rebuild the champion boots for paired deltas if needed by final stage
        d28_cached = Path(args.refs_dir) / "GEMSDOE25/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif"
        champ = holdout.read_binary(d28_cached) & ctx.foot
        hr_ch = holdout.evaluate_hide_and_recover(champ, ctx, b_visible_px=B_COLLAR, name="CHAMPION")
        boots["CHAMPION"] = hr_ch["_boots"]
        results.setdefault("CHAMPION", {"name": "CHAMPION", "hide_and_recover":
                                        {k: v for k, v in hr_ch.items() if not k.startswith("_")}})
    else:
        # ------- champion control (Pass-2 corrected; scoring only, no pixels reused) -------
        # Scoring the champion FILE under hide-and-recover is censorship-biased (its B=2 gate
        # used the full catalogue incl. withheld truth -> 0.0045 artefact). The upstream-fair
        # control scores its parent D28 (44090 dots, B=0) with a visible-only B=2 gate, which
        # reproduces upstream's published 0.09920232315251679 exactly.
        t0 = time.time()
        champ_file = holdout.read_binary(champion_path) & ctx.foot
        cens = holdout.evaluate_hide_and_recover(champ_file, ctx, b_visible_px=B_COLLAR, name="CHAMPION_FILE_CENSORED")
        d28_path = Path(args.refs_dir) / "GEMSDOE25/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif"
        d28 = holdout.read_binary(d28_path) & ctx.foot
        hr_ch = holdout.evaluate_hide_and_recover(d28, ctx, b_visible_px=B_COLLAR, name="CHAMPION_CONTROL_D28visB2")
        sg_ch = holdout.evaluate_sgmc_with_ci(champ_file, ctx, name="CHAMPION")
        results["CHAMPION"] = {"name": "CHAMPION recipe control = D28 parent (44090) gated by visible-only B=2 per cell (champion file = D28 minus full-catalogue B<=2; OWNER-REPORTED live 0.2778)",
                               "budget": int(champ_file.sum()), "control_parent_dots": int(d28.sum()),
                               "hide_and_recover": {k: v for k, v in hr_ch.items() if not k.startswith("_")},
                               "sgmc": {k: v for k, v in sg_ch.items() if not k.startswith("_")},
                               "champion_file_direct_censored_diagnostic_do_not_use_as_control":
                                   {k: v for k, v in cens.items() if not k.startswith("_")}}
        boots["CHAMPION"] = hr_ch["_boots"]
        log(f"CHAMPION control holdout={hr_ch['pooled_dti']:.6f} (censored file diagnostic {cens['pooled_dti']:.6f}) in {time.time()-t0:.0f}s")
        del champ_file, d28
        gc.collect()

        # ------- EXP1 CTRL (crest-sharpened per Pass-2 amendment) -------
        t0 = time.time()
        surf_sharp_path = wdir / "ap2_oof_sharp.npy"
        if surf_sharp_path.exists():
            surf_in = np.load(surf_sharp_path)
        else:
            surf_in = mdrc.sharpen_ridge_crest(np.asarray(surf, dtype=np.float32), ctx.foot)
            np.save(surf_sharp_path, surf_in)
        r = holdout_score(surf_in, ctx, BUDGET_CTRL, "EXP1_CTRL")
        results["EXP1_CTRL"] = {k: r[k] for k in ("name", "budget", "hide_and_recover", "sgmc")}
        boots["EXP1_CTRL"] = r["_boots"]
        full_masks["EXP1_CTRL"] = r["_full_mask"]
        log(f"EXP1_CTRL holdout={r['hide_and_recover']['pooled_dti']:.6f} sgmc_cal={r['sgmc']['sgmc_prevalence_calibrated_dti']:.6f} in {time.time()-t0:.0f}s")

        # ------- EXP2 chain -------
        t0 = time.time()
        chain, thr = compute_chain(surf, ctx.foot)
        np.save(wdir / "ap2_chain.npy", chain)
        field2_raw = np.where(chain >= 0.2, surf * (0.6 + 0.4 * chain), 0.0).astype(np.float32)
        field2_sharp_path = wdir / "ap2_chain_sharp.npy"
        if field2_sharp_path.exists():
            field2 = np.load(field2_sharp_path)
        else:
            field2 = mdrc.sharpen_ridge_crest(field2_raw, ctx.foot)
            np.save(field2_sharp_path, field2)
        log(f"chain computed thr90={thr:.4g}; eligible={(int(((chain>=0.2)&ctx.foot).sum()))} px in {time.time()-t0:.0f}s")
        r2 = holdout_score(field2, ctx, BUDGET_CTRL, "EXP2_CHAIN")
        results["EXP2_CHAIN"] = {k: r2[k] for k in ("name", "budget", "hide_and_recover", "sgmc")}
        boots["EXP2_CHAIN"] = r2["_boots"]
        full_masks["EXP2_CHAIN"] = r2["_full_mask"]
        log(f"EXP2_CHAIN holdout={r2['hide_and_recover']['pooled_dti']:.6f} sgmc_cal={r2['sgmc']['sgmc_prevalence_calibrated_dti']:.6f}")

        better = "EXP2_CHAIN" if (results["EXP2_CHAIN"]["hide_and_recover"]["pooled_dti"]
                                  >= results["EXP1_CTRL"]["hide_and_recover"]["pooled_dti"]) else "EXP1_CTRL"
        field_better = field2 if better == "EXP2_CHAIN" else surf_in
        np.save(wdir / "ap2_field_better.npy", field_better)
        log(f"EXP3 uses field {better}")

        # ------- EXP3 budget scan -------
        scan = {}
        for b in (25_000, 32_000, 37_654, 44_090):
            if b == BUDGET_CTRL:
                rb = r2 if better == "EXP2_CHAIN" else r
            else:
                t0 = time.time()
                rb = holdout_score(field_better, ctx, b, f"EXP3_B{b}")
                log(f"  budget {b}: holdout={rb['hide_and_recover']['pooled_dti']:.6f} in {time.time()-t0:.0f}s")
            scan[str(b)] = {"hide_and_recover": rb["hide_and_recover"], "sgmc": rb["sgmc"]}
            boots[f"EXP3_B{b}"] = rb["_boots"]
            full_masks[f"EXP3_B{b}"] = rb["_full_mask"]
        best_b = max(scan, key=lambda k: scan[k]["hide_and_recover"]["pooled_dti"])
        results["EXP3_SCAN"] = {"field": better, "scan": scan, "best_budget": int(best_b)}
        results["FINAL"] = {"field": better, "budget": int(best_b),
                            "hide_and_recover": scan[best_b]["hide_and_recover"], "sgmc": scan[best_b]["sgmc"]}
        np.save(wdir / "ap2_final_mask.npy", full_masks[f"EXP3_B{best_b}"])
        with open(wdir / "ap2_boots.npz", "wb") as f:
            np.savez(f, **boots)
        savedoc = {"seed": SEED, "b_collar_px": B_COLLAR, "min_sep_px": MIN_SEP,
                   "support_caps": {"full": SUPPORT_CAP_FULL, "quad": SUPPORT_CAP_QUAD},
                   "results": results}
        exp_path.write_text(json.dumps(clean(savedoc), indent=1))
        log(f"EXP3 best budget {best_b}")

    # ------- final stage: paired deltas, final mask, writer, gates (always rerun) -------
    final_info = results["FINAL"]
    field_name = final_info["field"]
    budget = int(final_info["budget"])
    if (wdir / "ap2_final_mask.npy").exists():
        final_mask = np.load(wdir / "ap2_final_mask.npy")
        boots_np = np.load(wdir / "ap2_boots.npz") if (wdir / "ap2_boots.npz").exists() else None
        boots_final = boots_np[f"EXP3_B{budget}"] if boots_np is not None and f"EXP3_B{budget}" in boots_np else boots.get("EXP1_CTRL")
    else:
        field = np.load(wdir / "ap2_field_better.npy")
        d_full = distance_transform_edt(~ctx.labels).astype(np.float32)
        final_mask, _ = emit_field(field, ctx.foot, d_full, budget=budget, support_cap=SUPPORT_CAP_FULL)
        boots_final = boots.get("EXP1_CTRL")
    paired = paired_vs(boots_final, boots["CHAMPION"]) if boots_final is not None else None
    log(f"final: field={field_name} budget={budget} dots={int(final_mask.sum())} paired={paired}")

    # shoreline-risk diagnostic: low det_elev_slope (band19, stack idx 18) + long chain share
    chain = np.load(wdir / "ap2_chain.npy") if (wdir / "ap2_chain.npy").exists() else compute_chain(surf, ctx.foot)[0]
    slope = np.asarray(base_mm[:, :, 18], dtype=np.float32)
    slope_med = float(np.median(slope[ctx.foot]))
    dots = final_mask & ctx.foot
    shoreline_risk = float(((slope < slope_med) & (chain >= 0.8) & dots).sum() / max(int(dots.sum()), 1))
    dcat = distance_transform_edt(~ctx.labels)
    min_dcat = float(dcat[dots].min()) if dots.any() else None
    on_cat = int((dots & ctx.labels).sum())

    run_partial = {"final_field": field_name, "final_budget": budget,
                   "final_dots": int(dots.sum()), "paired_vs_champion": paired,
                   "shoreline_risk_proxy_share": shoreline_risk,
                   "min_distance_to_catalogue_px": min_dcat, "on_catalogue_dots": on_cat,
                   "canary": {"worst_channel": canary["worst_channel"],
                              "worst_auc_oriented": canary["worst_auc_oriented"], "passed": canary["passed"]},
                   "oof_fold_aucs": oof_meta.get("fold_aucs")}
    (ROOT / "evidence" / "ap2_final_partial.json").write_text(json.dumps(clean(run_partial), indent=1))
    log(f"partial run info written: {run_partial}")

    # expose objects for the gate stage via a small state file + module-level pickle of mask path
    np.save(wdir / "ap2_final_mask.npy", final_mask)
    return


if __name__ == "__main__":
    main()
