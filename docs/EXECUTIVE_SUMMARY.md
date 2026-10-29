# Executive Summary — Consolidated GEMS / ApartGEMSDOE2 Decision

**Updated 2026-10-28 (`H-SARPU` session on `arena/431d4f24-apartgemsdoe2`).** This canonical decision document consolidates all `ApartGEMSDOE2` lanes (`H-SARPU`, `H-TRACE`, `H-UDSR`, `AP2`, `AP-1`, and the withdrawn `H2` seeded demo).

## Decision at a glance

> **Validated Unique GeoTIFF Deliverable (`H-SARPU EXP-2`):**
> `docs/downloads/apartgemsdoe2-sarpu-exp2-lefm-sarpu-37654dots-20261028T235500Z-25593731-zeros.tif` (`SHA-256: 030153b3bd16fb04eef1afa95f8931f27cd132e645c6825309e197cd3a85aa82`) + `.zip` + `-nan.tif` twin.
>
> - **Scientific Gates (`G1 + G2 + G3a + G4`): ALL PASS** — **ONLY candidate in `ApartGEMSDOE2` history** to achieve an all-time repository holdout record (**`HOLDOUT-DTI = 0.113838 > 0.113696`**, paired `Δ = +0.014636` vs `D28_B2`, 95% CI `[+0.005143, +0.024204]`, `99.9%` bootstrap win; Detached-600m `0.086337 > 0.083437`; `SGMC-CAL = 0.063808`), pass the 67-channel Leakage Canary (`0.7729 <= 0.90`), pass strict `[0, 1]` finite GeoTIFF validation (`12,279,160 / 12,279,160` finite `float32`), AND pass **genuine non-lattice uniqueness across all 559 extended-registry rasters + 8 local rasters** (`max |Spearman| = 0.1185 <= 0.90`, `worst sparse <= 3 px = 61.91% <= 70%`, `53.71% <= 70%` vs `<=50k`-dot peers, **`37.31% <= 70%` vs `GEMSDOE32 B2`**).
> - **Literal Calibration-Lattice Gate (`G3b`): FAIL-CLOSED (`verdict: "negative"`)** — strictly under uncalibrated literal Rule 1 against the 206,895-dot synthetic `r13-lattice-s5` grid (`99.87%` 3-px footprint coverage → `99.82%` literal overlap; null-calibrated excess is **`-0.3829 <= 0.70` PASS**). Automatic upload remains fail-closed unless a human selector explicitly applies the null-calibrated `s5` lattice rule.

## Auditable Deliverable & Uniqueness Table

Hidden-leaderboard estimates remain **`null`** for every unsubmitted file (a projection is never presented as a score).

| File | `HOLDOUT-DTI` (`GEMSDOE32-HIDE-RECOVER-v3.0`, n=22,232) | Hidden-board estimate | Non-Lattice Sparse Uniqueness (559 rasters) | Literal `s5` Lattice (`99.87%` cov) | Gate Status |
|---|---|---|---|---|---|
| **`docs/downloads/apartgemsdoe2-sarpu-exp2-lefm-sarpu-37654dots-20261028T235500Z-25593731-zeros.tif` (`H-SARPU EXP-2`, Selected)** | **`0.113838`** `[0.09999, 0.12708]` (**Repo Record**; `Δ+0.01464` vs `D28_B2`) | `null` | **PASS (`61.91% <= 70%`; `37.31%` vs `B2`)** | `99.82%` literal (`-0.3829` null excess) | **G1+G2+G3a+G4 PASS** (`verdict: negative` on literal `s5`) |
| `docs/downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif` (`H-UDSR EXP-3`) | `0.094698` `[0.08224, 0.10731]` | `null` | PASS (`69.42% <= 70%`) | `99.85%` | **NO** (Failed G2 & G3b) |
| `docs/downloads/apartgemsdoe2-trace-exp-2-trace-t1-22438dots-20261028T063240Z-71a21036-zeros.tif` (`H-TRACE EXP-2`) | `0.089333` `[0.07375, 0.10519]` | `null` | **FAIL (`86.26% > 70%`)** | `99.86%` | **NO** (Failed G2, G3a, G3b) |
| `docs/downloads/apartgemsdoe2-ap2-oofctrl-44090dots-20261027T220804Z-5e265df9-zeros.tif` (`AP2`) | `0.106024` `[0.0907, 0.1219]` | `null` | **FAIL (`74.50% > 70%`)** | `99.90%` | **NO** (Failed G3a, G3b) |
| `docs/downloads/apartgemsdoe2-ap1-dilatcond-37654-20261027-1f26aa05-zeros.tif` (`AP-1`) | `0.038911` `[0.0282, 0.0491]` | `null` | PASS | `99.72%` | **NO** (Failed G2, G3b) |
| `gems-h2-fractal-faultzone-*` (`H2` PR #20 demo) | `null` (seeded pseudo-features; withdrawn) | `null` | Not measured | Not measured | **NO** (DO NOT SUBMIT) |
| Historical focus-site bests (`GEMSDOE24..36`) | `0.00452–0.09920` (`USER-REPORTED` LB `0.2449–0.2778`) | — | **FAIL (`86.7%–100.0%`)** | `>99%` | **NO** (Historical duplicates) |

## Pre-Registered 3-Experiment `H-SARPU` Factorial Results

| Experiment | `HOLDOUT-DTI` [95% CI] | Detached-600m DTI | `SGMC-CAL-v3.0` DTI | Surface max \|Spearman\| | Worst Non-Lattice Sparse &le;3px |
|---|---|---|---|---|---|
| `EXP-1` · `SARPU-PureBlind-38k` (65/60 pure-physical ch.) | `0.087605` `[0.07312, 0.10198]` | `0.068812` | `0.060122` | `0.1211` | `53.99%` (&le;70% PASS) |
| **`EXP-2` · `SARPU-LEFM-Uncapped-38k` (Selected, 67/62 ch.)** | **`0.113838`** `[0.09999, 0.12708]` | **`0.086337`** | **`0.063808`** | **`0.1185`** | **`61.91%` (&le;70% PASS)** |
| `EXP-3` · `SARPU-TwoRegime-Balanced-38k` (42% collar cap) | `0.092213` `[0.07836, 0.10556]` | `0.071282` | `0.061223` | `0.1212` | `51.06%` (&le;70% PASS) |
| Control · `D28_B2` (Fold-Honest `B=2 px`) | `0.099202` `[0.08595, 0.11267]` | `0.083437` | `0.064121` | — | Historical reference |

## Step-by-Step Verification & DrivenData Upload Guide

1. **Verify SHA-256:** `sha256sum docs/downloads/apartgemsdoe2-sarpu-exp2-lefm-sarpu-37654dots-20261028T235500Z-25593731-zeros.tif` → must equal `030153b3bd16fb04eef1afa95f8931f27cd132e645c6825309e197cd3a85aa82`.
2. **Run Automated Saved-Byte Validator:** `python scripts/validate_submission.py docs/downloads/apartgemsdoe2-sarpu-exp2-lefm-sarpu-37654dots-20261028T235500Z-25593731-zeros.tif` → confirms `GTiff`, `1` band, `float32`, `EPSG:32611`, `3730×3292`, `12,279,160 / 12,279,160` finite in `[0.0, 1.0]`, `0` NaN in footprint, and `0` positive pixels on `labels.tif` (eliminating `"Predicted values must be in range [0, 1]"`).
3. **Human Selector Check:** Confirm weekly DrivenData slot budget (max 3 / rolling 7 days) and explicit authorization of null-calibrated `r13-lattice-s5` uniqueness (`-0.3829 <= 0.70`).
4. **DrivenData Submission Name & Note (`117/140` chars):**
   - Name: `apartgemsdoe2-sarpu-exp2-lefm-sarpu-37654dots-20261028T235500Z-25593731-zeros`
   - Note: `ApartGEMSDOE2 H-SARPU EXP-2: 67ch SAR-PU + 5-fold Williams/Crider LEFM + Baranov/GeoDAWN, 37654 dots B2 (HR 0.1138)`
