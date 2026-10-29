# Executive Summary — Consolidated GEMS / ApartGEMSDOE2 Decision

**Updated 2026-10-28 (`H-SPMD` session on `arena/9d6c28d5-apartgemsdoe2`).** This is the single canonical decision document for `ApartGEMSDOE2`. It supersedes earlier lane summaries and retains the 2026-10-28 fail-closed corrections (`docs/EXECUTIVE_SUMMARY_H2.md`, `docs/data/run_card_h2.json`, `assets/SUBMISSION_STATUS.txt`).

## Decision at a glance

> **Technical GeoTIFF Validity & Sparse Portfolio Uniqueness (`H-SPMD EXP-2`): PASS** (`34,500` binary dots, `12,279,160 / 12,279,160` finite `float32` pixels in `[0, 1]`, `0` NaN, `max |Spearman| = 0.1230 <= 0.90`, `max sparse 3-px overlap = 68.93% <= 70.0%` across all `543` sparse rasters in the `549`-raster 22-repo extended registry, **`HOLDOUT-DTI = 0.113181`** `[0.09960, 0.12562]` with **strictly positive paired 95% CI `[+0.000082, +0.027929]`** over fold-honest `D28_B2 = 0.099202` and **`+19.5%` lift** over `H-UDSR EXP-3 = 0.094698`).
>
> **Autonomous Competition Slot Verdict: `negative` — DO NOT AUTO-SUBMIT (HOLD FOR HUMAN PORTFOLIO SELECTOR).**
> 1. **Protocol Rule 6:** Competition slot allocation is reserved to a separate human portfolio selector step (weekly DrivenData cap = 3 submissions).
> 2. **Literal Zero-Exemption Lattice Gate (`IR-47`):** Against the `206,895`-dot `GEMSDOE24:13GEMSDOE` calibration lattice (which covers `99.8713%` of the footprint within 3 px), any `>= 22,164`-dot raster mathematically exceeds `70%` (`99.85% > 70%`), and `2 / 549` upstream registry TIFFs are malformed (`audit_complete = False`).
> 3. **Template Provenance:** In this network-restricted sandbox, `sample_submission.tif` was verified against SHA-256-pinned mirrors; re-verify saved bytes against a fresh authenticated DrivenData download before any portal upload.
>
> **If a human selector chooses to submit one `ApartGEMSDOE2` candidate** after fresh DrivenData template verification and cross-lane portfolio comparison against `GEMSDOE32 B2` (`0.2778` user-reported), **`apartgemsdoe2-spmd-exp-2-sarpu-unified-34500dots-20261028T235800Z-2a51285d-zeros.tif` (or `.zip`) is the single recommended valid, sparse-unique candidate from this repository.** Never submit historical `GEMSDOE24–36` files, `AP-1`, `AP2`, `H2`, `H-TRACE`, or duplicate `H-SPMD EXP-1`.

---

## 1. Complete Comparison Table: `ApartGEMSDOE2` Deliverables + 9 Focus Sites

Hidden-leaderboard score projections are **`null` (not estimable)** for every unsubmitted file per Protocol Rule 3 (*never write a projection as a score*). Every number below is explicitly labeled **`HOLDOUT-DTI`** (`GEMSDOE32-HIDE-RECOVER-v3.0`, `n=22,232` withheld positives; `GEMSDOE32-SGMC-CAL-v3.0`, `n=62,703`) or **`USER-REPORTED / UNVERIFIED`**.

| Site / Run | Exact File | `HOLDOUT-DTI` (`HIDE-RECOVER-v3.0`) | `SGMC-CAL-v3.0` / Claim | Uniqueness vs Extended Registry (`549` rasters) | Unmistakable Download / Submit Decision |
|---|---|---|---|---|---|
| **ApartGEMSDOE2 (`H-SPMD EXP-2` · Latest)** | `docs/downloads/apartgemsdoe2-spmd-exp-2-sarpu-unified-34500dots-20261028T235800Z-2a51285d-zeros.tif` (+ `.zip`, `-nan.tif`) | **`0.11318`** `[0.09960, 0.12562]` (paired Δ vs `D28_B2`: **`+0.01398` `[+0.00008, +0.02793]`**; `EXP-1` ctrl: **`0.12718`**) | `SGMC_cal`: `0.04797` `[0.04068, 0.05628]`; LB est: `null` | **Sparse PASS (`68.93% <= 70%`)** across `543` sparse rasters; surface `\|ρ\| = 0.1230 <= 0.90`; literal lattice `99.85%` | **DO NOT AUTO-SUBMIT (`verdict: negative`)** — **HOLD FOR HUMAN SELECTOR** (repo's best valid sparse-unique `.tif`) |
| **ApartGEMSDOE2 (`H-UDSR EXP-3`)** | `docs/downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif` | `0.09470` `[0.08224, 0.10731]` | `SGMC_cal`: `0.03981`; LB est: `null` | Sparse PASS (`69.42% <= 70%`); literal lattice `99.85%` | **DO NOT SUBMIT** (Superseded by `H-SPMD EXP-2` `+0.01848`) |
| **ApartGEMSDOE2 (`H-TRACE EXP-2`)** | `docs/downloads/apartgemsdoe2-trace-exp-2-trace-t1-22438dots-20261028T063240Z-71a21036-zeros.tif` | `0.08933` `[0.07375, 0.10519]` | `SGMC_cal`: `0.03903`; LB est: `null` | **NO** — `86.26% > 70%` sparse overlap | **DO NOT SUBMIT** |
| **ApartGEMSDOE2 (`AP2` / `AP-1` / `H2`)** | `apartgemsdoe2-ap2-*`, `apartgemsdoe2-ap1-*`, `gems-h2-fractal-*` | `0.1060` / `0.0389` / `null` (pseudo-demo) | LB est: `null` (H2 projection withdrawn) | **NO** (`74.5%` Arena8a / `99.72%` lattice / unmeasured) | **DO NOT SUBMIT** |
| **GEMSDOE32** | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (`37,654` dots) | `0.00452` static / `0.09920` fold-honest `B=2` | **`0.2778`** (`USER-REPORTED / UNVERIFIED`) | **NO** — `100.0%` subset of `GEMSDOE31` | **DO NOT SUBMIT** (Historical duplicate) |
| **GEMSDOE36** | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` (`38,854` dots) | `0.00458` static | `0.2750` (`USER-REPORTED / UNVERIFIED`) | **NO** — `97.4%` within 3 px of `GEMSDOE32` | **DO NOT SUBMIT** (Historical duplicate) |
| **GEMSDOE28** | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` (`37,660` dots) | `0.02936` static | `0.2710` (`USER-REPORTED / UNVERIFIED`) | **NO** — `95.5%` within 3 px of `GEMSDOE32` | **DO NOT SUBMIT** (Historical duplicate) |
| **GEMSDOE31** | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` (`40,199` dots) | `0.03052` static | `0.2708` (`USER-REPORTED / UNVERIFIED`) | **NO** — `95.4%` within 3 px of `GEMSDOE32` | **DO NOT SUBMIT** (Historical duplicate) |
| **GEMSDOE33** | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` (`41,865` dots) | `0.05197` static | `0.2632` (`USER-REPORTED / UNVERIFIED`) | **NO** — `92.6%` within 3 px of `GEMSDOE32` | **DO NOT SUBMIT** (Historical duplicate) |
| **GEMSDOE25** | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` (`44,090` dots) | `0.09674` static / `0.09920` `B=2` | `0.2600` (`USER-REPORTED / UNVERIFIED`) | **NO** — `100.0%` identical to `GEMSDOE30` | **DO NOT SUBMIT** (Historical duplicate) |
| **GEMSDOE30** | `gemsdoe30-d28-poisson300m-offcat-44090-20261003-8cf893ea-zeros.tif` (`44,090` dots) | `0.09674` static / `0.09920` `B=2` | `0.2600` (`USER-REPORTED / UNVERIFIED`) | **NO** — `100.0%` identical to `GEMSDOE25` | **DO NOT SUBMIT** (Historical duplicate) |
| **GEMSDOE24** | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` (`60,069` dots) | `0.09315` static | `0.2477` (`USER-REPORTED / UNVERIFIED`) | **NO** — `88.5%` within 3 px of `GEMSDOE32` | **DO NOT SUBMIT** (Historical duplicate) |
| **GEMSDOE27** | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` (`61,328` dots) | `0.09275` static | `0.2449` (`USER-REPORTED / UNVERIFIED`) | **NO** — `86.7%` within 3 px of `GEMSDOE32` | **DO NOT SUBMIT** (Historical duplicate) |

---

## 2. What `H-SPMD` Executed (3 Pre-Registered Experiments, `knowledge/preregistration_spmd_20261028.md`)

Following the recorded next step from PR #21 (`H-TRACE` proved geometry-only trace reshaping degrades holdout and that the remaining lever is **PU de-confounding + new subsurface/alteration detection physics**), we pre-registered 4 ranked geological hypotheses (`#1 H-SPMD`, `#2 H-DRAPE`, `#3 H-ANISO`, `#4 H-INSAR`), passed all **63 features** through the single-feature Leakage Canary (`max_oriented_auc = 0.769315 <= 0.90`; `evidence/spmd_leakage_canary_63ch.json`), and executed the exact 3-experiment factorial (`evidence/spmd_three_experiments_20261028.json`):

| Experiment | `HOLDOUT-DTI` [95% CI] | Paired Δ vs `D28_B2` (`0.09920`) | `SGMC-CAL-v3.0` | Emitted Dots (`>15 px` share) | Surface `max \|ρ\|` | Worst Sparse 3-px (`543` rasters) |
|---|---|---|---|---|---|---|
| **`EXP-1` (`SPMD-Sup61-Ctrl`)** | **`0.12718`** `[0.11552, 0.13864]` | **`+0.02798`** `[+0.01559, +0.04003]` | `0.05033` | `34,500` (`16.7%`) | `0.1277` (PASS) | `74.78%` (**FAIL — DUP**) |
| **`EXP-2` (`SPMD-SARPU-Unified`, emitted)** | **`0.11318`** `[0.09960, 0.12562]` | **`+0.01398`** `[+0.00008, +0.02793]` | `0.04797` | `34,500` (`22.2%`) | `0.1230` (PASS) | **`68.93%` (PASS)** |
| **`EXP-3` (`SPMD-SARPU-TwoRegime`)** | `0.09916` `[0.08659, 0.11110]` | `−0.00005` `[−0.01275, +0.01233]` | `0.04865` | `33,600` (`38.1%`) | `0.1063` (PASS) | **`65.30%` (PASS)** |

---

## 3. Why `GEMSDOE32` (`0.2778`) Leads the 9 Focus Sites & What `> 0.3195` / `0.4544` Requires

Full mathematical and structural derivation: `docs/research/why-02778-and-how-to-beat-it-20261028.md`.
- **Exact byte identity:** Pixel-wise XOR proves `GEMSDOE32 B2 == GEMSDOE28 D2.8 ∧ (d_catalogue > 2.0 px)` (`37,654` vs `44,090` dots in `GEMSDOE25/30`). Removing `6,436` near-catalogue flank dots (`d <= 200 m` from masked known faults) cut `0.2 × 6,436 = 1,287.2` from the `DTI` denominator while losing virtually zero numerator credit because unmapped fault continuations beyond the masked trace are already covered by dots at `200–280 m`.
- **Break-even economics (`α=0.2, β=0.8`):** A marginal dot improves `DTI` iff its expected 300 m triangular kernel credit exceeds `τ*(DTI) = 0.2·DTI / (1 − 0.8·DTI)` (`0.0714 TP/dot` at `0.2778`; `0.1428 TP/dot` at the live public #1 `0.4544`, which supersedes the prompt-cited `0.3195` and `0.4413`).
- **What beating `0.2778` and approaching `0.4544` requires:** Recovering **concealed intrabasin, piedmont-drape, and hydrothermal relay faults** beneath Quaternary valley fill where 100 m DEM scarps vanish — requiring both multi-depth geophysical/geochemical signal (`TMI - TMI_up150`, updip gravity/RTP/MT migration, Dickson-Scott `Th/K–U/Th`, 1 m LiDAR subtle grabens) and **SAR-PU propensity de-confounding** so training does not treat unmapped basin faults as true negatives.

---

## 4. Exact Submission Metadata (Only If Selected by Human Portfolio Selector)

1. **File:** `docs/downloads/apartgemsdoe2-spmd-exp-2-sarpu-unified-34500dots-20261028T235800Z-2a51285d-zeros.tif` (or `.zip`)
2. **SHA-256:** `d12ff10f7a0753d3c9c27b2030e195ce6c9ad5be23ac23cfaa8fdebb995628e6`
3. **Unique Submission Name:** `apartgemsdoe2-spmd-exp-2-sarpu-unified-34500dots-20261028T235800Z-2a51285d-zeros`
4. **Submission Note (`110 <= 140` chars):** `ApartGEMSDOE2 H-SPMD EXP-2: SAR-PU spy+propensity 61/55ch DualCover + TMI-bandpass/epithermal/LiDAR, 34500d B2`
5. **Pre-upload verification:** Re-run `.venv/bin/python scripts/check_submission.py docs/downloads/apartgemsdoe2-spmd-exp-2-sarpu-unified-34500dots-20261028T235800Z-2a51285d-zeros.tif --strict-finite` against an authenticated DrivenData `sample_submission.tif` download, then log the DrivenData submission-page receipt before relabeling any score as `ORGANIZER-CONFIRMED`.
