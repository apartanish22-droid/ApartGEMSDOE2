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

## Submission guide—future candidates only

1. Establish an explicitly assigned lane and budget; authenticate the organizer input files, sample and footprint; use the pinned shared feature stack and resolve upstream evaluator/writer/registry defects centrally.
2. Withhold whole fault segments with the requested buffer, build every catalogue-derived feature from visible faults only, and run single-feature leakage canaries. Compare pooled HOLDOUT-DTI and a paired spatial 95% interval against a frozen, same-fold incumbent.
3. Check the continuous surface against **every** verified registry raster **before** placing dots; stop on correlation above 0.90. Then check all final dots and stop if more than 70% are within three pixels of any registry raster. Do not exempt the lattice.
4. Reopen saved bytes against an authenticated template: single float32 GeoTIFF, matching CRS/shape/transform, finite [0,1] and no masks/NaNs inside the footprint, null/NaN outside under the published format. Resolve any portal-format ambiguity with the organizer; a local check does not prove acceptance.
5. Only a separate selector, after every gate and current authenticated weekly allowance are verified, may approve a unique name and note ≤140 characters. If approved, upload that exact file and save the submission-page receipt with the raster SHA-256. **Current status: no selector approval and no slot used.**

[Official problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [Official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) · [Organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) · [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) · [DOE INGENIOUS](https://gdr.openei.org/submissions/1391).
