# Executive summary and submission guide — 28 October 2026

> **DO NOT SUBMIT: no file is approved.** No new experiment, TIFF or weekly slot was used in this review. An authenticated organizer template, complete registry, explicit lane and valid buffered holdout remain unavailable. [Current JSON run card](../evidence/current_run_card.json) · [Full review](REVIEW_20261028_FOLLOWUP.md) · [Web scorecard](index.html#scorecard).

## Historical nine-site comparison

Every numeric score below is **USER-REPORTED / UNVERIFIED**, not an organizer-confirmed file receipt. Links point to pinned archival variants used for the geometry audit; the archived encoding/name may differ from the submitted file. The "unique" column is directional overlap with a second archived focus-site raster, not a complete registry test. Hidden-board estimates are unavailable for any new file. All files are **research only**.

| Site | Reported file / archival research variant | Claimed value | New-file estimate | Unique vs 8 peers? | Submit? |
|---|---|---:|---|---|---|
| GEMSDOE24 | [`h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan`](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/2521cb676e172c141a4417e4925b73b6a896c1eb/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif) | 0.2477 | Not estimable | No: 100.0% vs GEMSDOE25 | No |
| GEMSDOE25 | [`dotted-h19-5-d2-8-20261002-e56ea318af89-nan`](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/5a60fb475b7171af93cfce795abe6d96c4021ea2/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif) | 0.2600 | Not estimable | No: 100.0% vs GEMSDOE24 | No |
| GEMSDOE27 | [`topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan`](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/4d39bbf92edd51fdf47004df5873793a035592e5/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif) | 0.2449 | Not estimable | No: 98.0% vs GEMSDOE24 | No |
| GEMSDOE28 | [`h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan`](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/67dbdf4da84fc92a98dd9644ab816ed18ae36bcc/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif) | 0.2710 | Not estimable | No: 100.0% vs GEMSDOE24 | No |
| GEMSDOE30 | [`d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca`](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/3c3d7255fdbb3a94375eff086522463a8eaca449/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | 0.2600 | Not estimable | No: 100.0% vs GEMSDOE24 | No |
| GEMSDOE31 | [`h27-4-solo-d28-20261004-8acb75e1-nan`](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/abd9a45cc7adf046d7d3829eb6e8c980943f462d/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif) | 0.2708 | Not estimable | No: 100.0% vs GEMSDOE24 | No |
| GEMSDOE32 | [`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/1398109a23f04a2ace71c1bd2f527cfba87860b5/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | 0.2778 | Not estimable | No: 100.0% vs GEMSDOE24 | No |
| GEMSDOE33 | [`h33d-analog-tip-stepover-r30-20261004-cb490425926e`](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/122e2240a835c9c84831943ee3489dbb48fd6e85/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | 0.2632 | Not estimable | No: 99.7% vs GEMSDOE27 | No |
| GEMSDOE36 | [`anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros`](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/61783525af4aa6dcf8da0bc68b06fa38b89ed27a/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | 0.2750 | Not estimable | No: 97.6% vs GEMSDOE27 | No |

[Full saved-byte evidence and all 72 comparisons](../evidence/historical_audit.json) were independently replayed from hash-pinned owner mirrors. The official public leaderboard was observed at **0.4544** on 28 October 2026, not bound to a specific file in this review and not guaranteed current. GEMSDOE32's 0.2778 is unverified; its collar-pruned geometry is consistent with, but does not prove, a false-positive-reduction explanation. [Corrected mechanism and algebra](research/why-02778-and-how-to-beat-it-20261028.md).

## Archived H-TRACE research artifact

[Research TIFF — DO NOT SUBMIT](downloads/apartgemsdoe2-trace-exp-2-trace-t1-22438dots-20261028T063240Z-71a21036-zeros.tif) · [ZIP — research only](downloads/apartgemsdoe2-trace-exp-2-trace-t1-22438dots-20261028T063240Z-71a21036-zeros.zip). SHA-256 `32716d4851e9de2df406eeb2386c8ddcf9aa970c985643c7e5484973dd023b4f`. A saved-byte recheck found **22,406 / 22,438 = 99.857%** overlap within three pixels of the registered lattice, so it fails the literal 70% gate. The earlier 0.1293 surface correlation is an incomplete prior report checked **after** placement, not a pre-placement pass.

The prior session reported **HOLDOUT-DTI 0.0893 [0.0737, 0.1052]**, evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld-positive occurrences. It is an archived numerical diagnostic, **not valid evidence under the requested buffered-whole-segment protocol**: this review independently found 15,705 occurrences within 15 pixels of visible faults, minimum separation 2 pixels in each cell, and 76 partially scored connected-component instances. This geometry check did not rerun the model or calculate a new DTI. [Split receipt](../evidence/shared_split_geometry_20261028.json) · [upstream issue #60](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/60).

The TIFF is one float32 band, EPSG:32611, 3730 × 3292, affine (100, 0, 243350, 0, −100, 4508550), finite [0,1] and unmasked within the owner-mirrored footprint. Its unmasked exterior zeros do **not** satisfy the conservative null/NaN-outside reading. The mirror is not authenticated and portal acceptance is unknown. Its archived name and 110-character note are in the run card for provenance only; **do not use them to upload**.

## Concurrent RAD-SCARP research artifact

Another session generated [RAD-SCARP](downloads/apartgemsdoe2-rad-scarp-offcatalogue-geothermal-20261028T224529Z-04053573-zeros.tif) while this review was underway. Its SHA-256 is `ce5295029b2f506bed5d49b74432370ba6101d5b810797be78af7502d41828f3`; an [independent saved-byte check](../evidence/rad_scarp_independent_recheck_20261028.json) found **10,421 / 10,457 = 99.66%** of its dots within three pixels of the registered lattice, exceeding the 70% limit. The generator used the full catalogue rather than fold-visible faults; the archived v3 diagnostic lacks a confidence interval and is not valid requested-protocol holdout evidence. The owner-mirrored grid is not organizer-authenticated; exterior zeros do not meet the conservative null/NaN-outside reading and portal acceptance is unknown. **Research only—DO NOT SUBMIT.**

## Three additional concurrent artifacts

A separate session generated three more TIFFs while this review was underway. None is eligible for a slot. Our [independent saved-byte recheck](../evidence/parallel_three_independent_recheck_20261028.json) measures the required directional overlap against the registered lattice; the previous calculation mistakenly counted lattice cells near the candidate rather than candidate cells near the lattice.

| Research-only file | Saved positive cells | Within 3 px of lattice | Decision |
|---|---:|---:|---|
| [H-DIL-GRAV TIFF](downloads/gemsdoe32-h-dil-grav-dilate-x-gravlow-top37654-20261028T224631Z-3df650f1-zeros.tif) | 36,975 | 36,692 / 36,975 = **99.23%** | DO NOT SUBMIT |
| [H-MAG-EDGE×SLOPE TIFF](downloads/gemsdoe32-h-mag-edge-slope-mag-x-slope-top37654-20261028T224750Z-2c00c25b-zeros.tif) | 5,103,418 | 5,098,478 / 5,103,418 = **99.903%** | DO NOT SUBMIT |
| [H-DEPTH×COND TIFF](downloads/gemsdoe32-h-depth-cond-conductive-under-thin-cover-top37654-20261028T224836Z-e34db98d-zeros.tif) | 5,106,385 | 5,099,871 / 5,106,385 = **99.872%** | DO NOT SUBMIT |

The last two exceeded their intended 37,654-cell budget because of tied threshold values. All three have finite unmasked [0,1] cells inside the owner-mirrored footprint, but exterior zeros and unknown portal acceptance; the historical shared-v3 diagnostics do not establish the requested buffered holdout. Their generators are blocked, and the full registry and authenticated organizer template remain unavailable.

## H-SPMD three-experiment research artifact (`arena/9d6c28d5-apartgemsdoe2`)

[Research TIFF — DO NOT SUBMIT](downloads/apartgemsdoe2-spmd-exp-2-sarpu-unified-34500dots-20261028T235800Z-2a51285d-zeros.tif) · [ZIP — research only](downloads/apartgemsdoe2-spmd-exp-2-sarpu-unified-34500dots-20261028T235800Z-2a51285d-zeros.zip) · [H-SPMD Run Card](../evidence/spmd_run_card_20261028.json) · [Preregistration](../knowledge/preregistration_spmd_20261028.md) · [Web brief](spmd/index.html).

- **SHA-256 (`-zeros.tif`):** `d12ff10f7a0753d3c9c27b2030e195ce6c9ad5be23ac23cfaa8fdebb995628e6` (`EPSG:32611`, `3730 × 3292`, single-band `float32` in `[0.0, 1.0]`, `12,279,160` finite pixels, `0` NaN, `34,500` footprint dots, `0` on visible `fault_mask`).
- **Matched v3 holdout diagnostic (`GEMSDOE32-HIDE-RECOVER-v3.0`, `n = 22,232` withheld occurrences; note unbuffered split caveat: `15,705 / 22,232` within `15 px` of visible faults):**
  - `EXP-1 (SPMD-Sup61-Ctrl)`: `HOLDOUT-DTI = 0.127184` `[0.11552, 0.13864]` (paired `+0.027982` vs `D28_B2 = 0.099202`), `34,500` dots, sparse 3-px max `74.78% > 70%` (**duplicate**).
  - **`EXP-2 (SPMD-SARPU-Unified)` [emitted]:** **`HOLDOUT-DTI = 0.113181` `[0.09960, 0.12562]`** (paired `+0.013978` `[+0.00008, +0.02793]` vs `D28_B2`; `+0.018483` vs prior sparse-unique `H-UDSR EXP-3 = 0.094698`), `34,500` dots (`22.17%` at `d > 15 px`, `23.63%` in LiDAR gaps, `0%` in deep playa), 63-ch leakage canary max oriented AUC `0.769315 <= 0.90`, pre-placement surface max `|Spearman| = 0.1230 <= 0.90`, **543-raster sparse 3-px max `68.93% <= 70%` (`WBGGEMSDOE3`, `0.98%` vs `RAD-SCARP`, `0.74%` vs `H-DIL-GRAV`)**, literal `13GEMSDOE` covering-lattice overlap **`99.852% > 70%` (`verdict: negative` — research only / DO NOT SUBMIT)**.
  - `EXP-3 (SPMD-SARPU-TwoRegime)`: `HOLDOUT-DTI = 0.099157` `[0.08659, 0.11110]`, `33,600` dots, sparse 3-px max `65.30% <= 70%`.
- **Archived provenance strings (do not upload without separate human selector approval):** name `apartgemsdoe2-spmd-exp-2-sarpu-unified-34500dots-20261028T235800Z-2a51285d-zeros`, note (`110` chars) `ApartGEMSDOE2 H-SPMD EXP-2: SAR-PU spy+propensity 61/55ch DualCover + TMI-bandpass/epithermal/LiDAR, 34500d B2`.

## H-SARPU three-experiment 67-ch Multi-Physics + Isomorphic LEFM artifact (`arena/431d4f24-apartgemsdoe2`)

[Validated GeoTIFF (-zeros, 198 KiB)](downloads/apartgemsdoe2-sarpu-exp2-lefm-sarpu-37654dots-20261028T235500Z-25593731-zeros.tif) · [ZIP bundle (164 KiB)](downloads/apartgemsdoe2-sarpu-exp2-lefm-sarpu-37654dots-20261028T235500Z-25593731-zeros.zip) · [NaN-exterior twin](downloads/apartgemsdoe2-sarpu-exp2-lefm-sarpu-37654dots-20261028T235500Z-25593731-nan.tif) · [H-SARPU Run Card](../evidence/sarpu_run_card_20261028.json) · [Preregistration](../knowledge/preregistration_sarpu_20261028.md) · [Web dashboard](sarpu/index.html) · [DrivenData step-by-step guide](sarpu/executive-summary.html).

- **SHA-256 (`-zeros.tif`):** `030153b3bd16fb04eef1afa95f8931f27cd132e645c6825309e197cd3a85aa82` (`EPSG:32611`, `3730 × 3292`, single-band `float32` in `[0.0, 1.0]`, `12,279,160 / 12,279,160` finite pixels, `0` NaN, `37,654` footprint dots, `0` on visible `fault_mask`, `13 / 13` automated checks passed).
- **Matched v3 holdout + Detached-600m + independent SGMC-CAL (`GEMSDOE32-HIDE-RECOVER-v3.0`, `n = 22,232`; `SGMC-CAL-v3.0`, `n = 62,703`; 67-ch leakage canary max oriented AUC `0.772907 <= 0.90`):**
  - `EXP-1 (SARPU-PureBlind-38k)`: `HOLDOUT-DTI = 0.087605` `[0.07312, 0.10198]`, Detached-600m `= 0.068812`, `SGMC-CAL = 0.060122`, sparse 3-px max `53.99% <= 70%`.
  - **`EXP-2 (SARPU-LEFM-Uncapped-38k)` [emitted — #1 sparse-unique score in repo]:** **`HOLDOUT-DTI = 0.113838` `[0.09999, 0.12708]`** (`> 0.113181` H-SPMD EXP-2 and `> 0.113696` H-UDSR EXP-2; paired `+0.014636` `[+0.00514, +0.02420]` vs fold-honest `D28_B2 = 0.099202`, `99.9%` win rate), **Detached-600m (`d >= 6 px`) `= 0.086337 > 0.083437`**, **independent `SGMC-CAL-v3.0 = 0.063808` (`+33.0%` over H-SPMD `0.047974`)**, `37,654` dots (`36.49%` at `d > 15 px`, `30.52%` in LiDAR gaps), pre-placement surface max `|Spearman| = 0.1185 <= 0.90`, **559-raster genuine non-lattice sparse 3-px max `61.91% <= 70%`** (`53.71%` across `<=50k`-dot peers, **`49.41%` vs H-SPMD EXP-2**, **`37.31%` vs `GEMSDOE32 B2`**, `0.77%` vs `RAD-SCARP`, `0.43%` vs `H-DIL-GRAV`), literal `13GEMSDOE` covering-lattice overlap **`99.82% > 70%`** (`-0.3829 <= 0.70` null-calibrated excess -> literal Run Card `verdict: negative` — do not auto-submit without human selector approval).
  - `EXP-3 (SARPU-LEFM-TwoRegime-38k)`: `HOLDOUT-DTI = 0.092213` `[0.07836, 0.10556]`, Detached-600m `= 0.071282`, `SGMC-CAL = 0.061223`, sparse 3-px max `51.06% <= 70%`.
- **Provenance strings (subject to human selector decision):** name `apartgemsdoe2-sarpu-exp2-lefm-sarpu-37654dots-20261028T235500Z-25593731-zeros`, note (`117` chars) `ApartGEMSDOE2 H-SARPU EXP-2: 67ch SAR-PU + 5-fold Williams/Crider LEFM + Baranov/GeoDAWN, 37654 dots B2 (HR 0.1138)`.

## Submission guide—future candidates only

1. Establish an explicitly assigned lane and budget; authenticate the organizer input files, sample and footprint; use the pinned shared feature stack and resolve upstream evaluator/writer/registry defects centrally.
2. Withhold whole fault segments with the requested buffer, build every catalogue-derived feature from visible faults only, and run single-feature leakage canaries. Compare pooled HOLDOUT-DTI and a paired spatial 95% interval against a frozen, same-fold incumbent.
3. Check the continuous surface against **every** verified registry raster **before** placing dots; stop on correlation above 0.90. Then check all final dots and stop if more than 70% are within three pixels of any registry raster. Do not exempt the lattice.
4. Reopen saved bytes against an authenticated template: single float32 GeoTIFF, matching CRS/shape/transform, finite [0,1] and no masks/NaNs inside the footprint, null/NaN outside under the published format. Resolve any portal-format ambiguity with the organizer; a local check does not prove acceptance.
5. Only a separate selector, after every gate and current authenticated weekly allowance are verified, may approve a unique name and note ≤140 characters. If approved, upload that exact file and save the submission-page receipt with the raster SHA-256. **Current status: no selector approval and no slot used.**

[Official problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [Official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) · [Organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) · [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) · [DOE INGENIOUS](https://gdr.openei.org/submissions/1391).
