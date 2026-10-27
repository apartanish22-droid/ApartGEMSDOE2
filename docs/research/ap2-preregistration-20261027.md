# AP2 preregistration — Chain-Corroborated Credit-Bar lane (2026-10-27)

Written **before** any AP2 experiment was run in this repository. This file fixes the lane,
the five ranked hypotheses, the three permitted experiments, and the promotion gates.
Numbers produced later must be reported against this text, not rewritten to fit it.

## 0. Why the champion scored 0.2778 (the question this session must answer first)

Forensically (byte-level, measured in GEMSDOE32 `evidence/d28_forensic_autopsy.json` and
GEMSDOE36 `evidence/forensics_champion.json` at the pinned commits in `registry/PROVENANCE.md`;
re-measured here in `evidence/ap2_focus9_forensics.json`), the champion
`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` (OWNER-REPORTED live 0.2778, no organiser receipt
in any repo reviewed) is **not a new geological detector**. It is the last step of a pure
emission-geometry ablation on one dense backbone:

| Step | Dots | OWNER-REPORTED live | Operation |
|---|---:|---:|---|
| H19-5 dense backbone | 121,131 | 0.1922 | multi-line corroborated ridge surface, thresholded |
| d1.5 | 60,069 | 0.2477 | BFS thinning, min spacing ≈1.5 px |
| d2.8 | 44,090 | 0.2600 | thinning, min spacing ≈2.4–2.8 px (≈300 m) |
| solo, B=1 | 40,199 | 0.2708 | d2.8 minus 3,891 dots ≤1 px from the catalogue |
| **h33-2, B=2** | **37,654** | **0.2778** | solo minus 2,545 dots ≤2 px from the catalogue |
| Anderson (GEMSDOE36) | 38,854 | 0.2750 | champion superset: all 37,654 champion dots + 1,200 extra |

Mechanism (official metric, DrivenData p.967): DTI = TPw / (TPw + 0.2·FPw + 0.8·FNw) with a
300 m (3 px) triangular kernel. A predicted pixel earns kernel credit for truth pixels within
300 m; a second pixel 100 m away earns almost no *additional* TPw (the max-kernel is already
≈satisfied) but pays almost its full 0.2·(1−k) FPw. Thinning 121,131 → 44,090 px therefore kept
75.9% of the 300 m kernel integral while cutting FP mass by 63.6% (measured). The B ladder then
deleted dots the organiser's known-fault masking renders near-worthless: inverting the three
live scores gives ≈0.002–0.016 credit per deleted near-catalogue dot, far below the break-even
for adding a dot, α·DTI ≈ 0.2 × 0.2778 ≈ **0.0556**. The 1,200 Anderson additions earned
≈0.014–0.023 per dot — also below break-even — hence 0.2750 < 0.2778.

**Conclusions that constrain any attempt to beat 0.2778:**
1. Emission geometry (spacing, catalogue buffer, budget, credit bar) is worth more verified
   live points (+0.0856 from 0.1922 → 0.2778) than any new surface tried since. A candidate that
   ignores it starts ≈0.08 behind.
2. The champion still wastes budget three measured ways: (a) 10,099/44,090 dots (22.9%) sat on
   isolated 1-px components of H19-5, 1,732 with zero corroboration from H19-4/H16-1/Ens12/LiDAR;
   (b) its thinning was score-blind row-major BFS; (c) its budget (37,654) is inherited, not
   derived from the credit bar. Faults are ≥1 km curvilinear objects; an isolated high pixel
   with no along-strike chain support is a priori unlikely to be one.
3. Beating 0.2778 therefore requires a surface whose *marginal credit per dot* is higher, or
   equal credit at lower mass. Holdout DTI on hidden catalogue segments is only a proxy: it
   rewards catalogue-style faults, while live truth is expert-mapped faults **absent** from the
   catalogue. The SGMC off-catalogue score is the second, independent proxy; both are reported,
   neither is called a live score.

## 1. The lane (single method paragraph — this session stays inside it)

**AP2-H1 (CCCB — Chain-Corroborated Credit-Bar):** a 4-quadrant out-of-fold (OOF)
HistGradientBoosting surface over the canonical 35-channel stack (`src/gems32/features.py`)
plus the 20 hash-pinned external uint8 channels (1 m LiDAR scarp 12, GeoDAWN radiometric
K/eTh/eU/TC 4, GeoDAWN extensions ThK/UK/UTh/TMI_up150 4), trained per fold on the other three
quadrants with positives = catalogue pixels, negatives = footprint pixels >3 px from any
catalogue pixel, and PU-aware negative weights (1.0 inside LiDAR-valid, 0.5 inside the LiDAR
gap, where "unlabelled" is least trustworthy); the OOF surface is then multiplied by a
label-free chain-corroboration factor — the maximum over 4 axes of the fraction of the 10
along-axis neighbours (±1…5 px) that lie in the surface's own top footprint decile — as
`field = oof × (0.6 + 0.4·chain)` with eligibility `chain ≥ 0.2`; dots are emitted by the
shared exact submodular emitter (`gems32.emitter.emit`, `min_sep_px = 2.8`, `B = 2`: distance to
catalogue > 2 px) and the budget is chosen by the credit-bar rule (EXP3), not inherited.
Named non-fault mimic: Pleistocene Lake Lahontan shoreline benches and basalt-flow margins —
elongated, chain-supported, topographically identical at 100 m; mitigated only partially by the
multi-physics features, so a shoreline-contamination diagnostic (share of dots on low-slope
contour-parallel chains) is reported, not hidden.

## 2. Five ranked candidate hypotheses (generated before implementing)

Ranking key: expected DTI improvement (prior, from §0 forensics) × probability / cost.
"Not tried" was checked against GEMSDOE32 `registry/hypotheses.json` (70 entries) and the nine
focus repos' downloads; items marked PARTIAL have a named predecessor and state the difference.

| Rank | ID | Layers | Physical signature / transform | Why it should catch a fault missing from USGS/INGENIOUS, not one already in it | Difference from this portfolio's prior work | Expected gain / cost |
|---:|---|---|---|---|---|---|
| 1 | **AP2-H1 CCCB** | 19 core bands → 35-ch stack; LiDAR u8 (`step_max, ex_max, downface_max, valid`…); GeoDAWN rad + extensions u8 | OOF HistGB posterior × along-axis chain vote (4 axes, ±5 px) on the surface's top decile; exact emitter, credit-bar budget | Experts mapped the live truth by *tracing lineaments*, i.e. chain continuity is part of the truth-generating process, while catalogue membership is irrelevant to the gate (applied identically at B>2 everywhere). Isolated speckles — the champion's measured FP load — are exactly what a human mapper would not draw. | Chain votes exist as *channels* (H33-C scarplet chain; MDRC `lidar_scarp_chain_500m`), never as a hard eligibility gate + multiplicative field applied to an OOF posterior with a credit-bar budget. H60-3 registered the credit bar abstractly; no repo shipped the combination. | High / medium (reuses stacks; CPU-only feasible) |
| 2 | AP2-H2 Prevalence-calibrated blind-basin reallocation | LiDAR `valid`; potential-field bands 3/5/13/18; SGMC u8 used **only** to measure prevalence, never as a feature | Split budget between LiDAR-valid (75.4%) and LiDAR-gap regimes in proportion to measured off-catalogue SGMC *prevalence* (≈1.61× denser in the gap), supervised surface in-valid, label-free worm rank in-gap | Gap basins are where pre-LiDAR mapping missed faults; the catalogue is 1.26× denser inside LiDAR, so area-proportional allocation (champion ≈76% in-valid) under-samples the gap relative to its fault density | PARTIAL: H45/H48 dual-cover used a fixed ≈30% gap quota with the same model class in both regimes; AP2-H2 derives the quota from measured prevalence and changes model class per regime. Deferred unless EXP1 shows a gap deficit, to stay in one lane. | Medium / medium |
| 3 | AP2-H3 Dip-migrated basement step | Band 15 `depth_to_base_surf` + gradient; bands 5/18 gravity; band 2 RTP | Shift potential-field worm crests basinward (direction of increasing depth-to-basement) by min(2 px, depth-scaled offset for a 60° normal fault) before emission | A buried 45–60° fault's geophysical edge sits updip of its surface trace; catalogue faults were mapped at the surface, so uncorrected worms systematically miss the blind trace by 150–300 m = the full kernel width | PARTIAL: H32-A/H44-5 used dip projection as one additive arm on the d2.8 backbone (never standalone, never depth-scaled per-pixel). Deferred (one lane). | Medium / low–medium |
| 4 | AP2-H4 Catalogue-difference (SGMC/Qfaults) gated emission | `derived_sgmc_faults_100m_u8`; GDR Qfaults traces CSV; bands 3/5/12 as corroboration | Emit SGMC traces absent from `labels.tif` (>300 m) only where ≥2 geophysical edges coincide within 300 m | Directly targets faults mapped by USGS state compilations but not in the competition catalogue | PARTIAL: repeatedly tried solo, live ≈0.05 (`sgmc-off-catalogue-44k`). Using SGMC as an *input* invalidates the SGMC evaluator, so it can only be a replacement pool, not this lane. Rejected for this session. | Low (measured) / low |
| 5 | AP2-H5 Seismicity-chain lineaments | Bands 10 `deq_n100a15`, 16 `ieq_n100a15`; free official source if raw catalogue needed: USGS ComCat FDSN `https://earthquake.usgs.gov/fdsnws/event/1/` (named, not fetched — sandbox egress blocks it, so **not viable here**) | Hough/Radon collinearity of earthquake-density ridges | Sub-surface faults with no scarp still host microseismicity | Solo AUC of bands 10/16 measured 0.55–0.57 in GEMSDOE32 canaries; raw-catalogue version is data-blocked in this sandbox. Rejected for this session. | Low / high (blocked) |

## 3. Experiments (budget: exactly 3, then stop)

All scored with the vendored canonical evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`
(`holdout.evaluate_hide_and_recover`, B-visible = 2, 22,232 withheld positives expected,
256-block cluster-bootstrap 95% CI, seed fixed) **and** `GEMSDOE32-SGMC-CAL-v3.0`.
The champion raster (from GEMSDOE32 downloads, hash-checked) is re-scored in the same run as
the control — for calibration only; **no champion pixel is copied into any candidate**.

- **EXP1 — canary + control.** Restore hash-pinned data; build stacks; leakage canary: every
  channel alone, pooled AUC on withheld-segment domains vs matched negatives (fail if > 0.90).
  Train the preregistered 4-quadrant OOF HistGB (max_iter 180, lr 0.07, leaves 31,
  min_samples_leaf 40, L2 0.1, seed 20261027; ≤60k pos / 240k neg per fold). CTRL emission:
  raw OOF field, budget 37,654, B=2, min_sep 2.8. Score CTRL + champion control.
- **EXP2 — chain gate.** Same OOF surface; CCCB field as in §1; same budget/emission. Score.
- **EXP3 — credit-bar budget.** Take the better field of EXP1/EXP2 (selection disclosed);
  budgets {25,000, 32,000, 37,654, 44,090}; pick the budget by holdout DTI, then build the final
  full-map mask from the (stationary) OOF field at that budget with full-catalogue B=2, write
  `-zeros` + `-nan` + zip via the canonical writer, and run every gate below. The OOF field is
  used for the final file (no holdout→live model switch).

## 4. Promotion gates (all must pass for verdict `promote` / 🟢 OK TO SUBMIT)

- **G1 format:** canonical 13-check validator passes on re-read bytes: single-band float32,
  3730×3292, EPSG:32611, template transform, **all** 12,279,160 cells finite and in [0,1] for
  the `-zeros` file (this is the exact check behind the portal error
  "Predicted values must be in range [0, 1]"), 0 dots on the catalogue.
- **G2 holdout:** candidate HOLDOUT-DTI (v3.0, B-vis 2) > champion control scored identically
  (point estimate), with the paired block-bootstrap ΔCI reported alongside (not hidden if it
  crosses 0 — then the verdict is `negative`).
- **G3 uniqueness (protocol rule 1):** vs each of the nine focus-site winners **and** vs the
  champion: surface Spearman |ρ| ≤ 0.90 before placement; final dots ≤ 70% within 3 px of that
  raster's dots. Synthetic covering lattices (e.g. r13-lattice-s5, 206,895 dots on a 5-px grid)
  are excluded from the *denominator* with the reason logged: any 37k-dot set is ~100% within
  3 px of a 5-px lattice by construction, so that literal check is mathematically vacuous
  (irregularity IR-AP2-02); lattice overlap is still measured and reported.
- **G4 leakage canary:** max single-channel AUC ≤ 0.90 (EXP1).
- **G5 construction:** on-catalogue dots = 0, min distance to catalogue > 2 px, budget and
  shoreline diagnostic reported.
- **G6 no-copy proof:** candidate dot set is not a subset/superset of any focus winner;
  sha256 differs from every registry raster checked; source surface saved as receipt stats.

If any gate fails, the verdict is `negative`, the banner is 🔴 DO NOT SUBMIT, and the negative
result is the deliverable. Per protocol rule 6, `promote` means "eligible for the separate
weekly-slot selector"; the site banner ⚠-labels that distinction in words a downloader cannot miss.

## 5. Score labelling

Every number is `HOLDOUT-DTI (evaluator, n withheld, 95% CI)`, `OWNER-REPORTED` (live scores
transcribed from the prompt/ledgers — no organiser receipts exist in the repos), or
`OFFICIAL-SNAPSHOT` (leaderboard page read directly this session). A projection, when shown at
all, is labelled `PROJECTION (not a score)` with the calibration method stated.
