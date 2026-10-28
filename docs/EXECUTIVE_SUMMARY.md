# Executive summary — GEMS fault discovery

**28 October 2026 · verdict: negative · submission approved: NO.** No new
geological experiment, original competition TIFF, holdout score or portal
submission was produced in this review. The requested unique, better-scoring
file remains unfulfilled. Do not substitute a renamed old file or a demo.
A concurrent branch generated a RAD-SCARP research TIFF, but an independent
saved-byte recheck shows **10,421/10,457 dots (99.66%)** overlap a pinned
lattice within three pixels; it fails the literal 70% limit. Its earlier
uniqueness-pass and portal-safe claims are withdrawn. A valid comparable
holdout with CI is not established. [Research-only TIFF](downloads/apartgemsdoe2-rad-scarp-offcatalogue-geothermal-20261028T224529Z-04053573-zeros.tif) ·
[saved-byte audit](../evidence/rad_scarp_saved_byte_recheck_20261028.json) ·
[current negative JSON card](../evidence/current_run_card.json).

## Nine priority sites

Each filename and historical score below is **user-reported / unverified**; no
organizer receipt binds it to bytes. "Best" means the supplied historical claim,
not independently verified leaderboard performance. Each linked brief identifies
the archived comparison variant and SHA-256, which may differ from the reported
upload. A new-file leaderboard estimate is **not estimable for every row**.
"Near" is directional: fraction of that archive's dots within three pixels of
one other focus-site raster (literal stop threshold 70%). It proves a failure
against that witness, not a complete all-registry audit.

| Site | Reported best file | Reported value | Unique? | Download / upload |
|---|---|---:|---|---|
| [GEMSDOE24](sites/gemsdoe24.html) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | NO — 100.0% near GEMSDOE25 | Research only; NO upload |
| [GEMSDOE25](sites/gemsdoe25.html) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | NO — 100.0% near GEMSDOE24 | Research only; NO upload |
| [GEMSDOE27](sites/gemsdoe27.html) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | NO — 98.0% near GEMSDOE24 | Research only; NO upload |
| [GEMSDOE28](sites/gemsdoe28.html) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | NO — 100.0% near GEMSDOE24 | Research only; NO upload |
| [GEMSDOE30](sites/gemsdoe30.html) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | NO — 100.0% near GEMSDOE24 | Research only; NO upload |
| [GEMSDOE31](sites/gemsdoe31.html) | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | NO — 100.0% near GEMSDOE24 | Research only; NO upload |
| [GEMSDOE32](sites/gemsdoe32.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | NO — 100.0% near GEMSDOE24 | Research only; NO upload |
| [GEMSDOE33](sites/gemsdoe33.html) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | NO — 99.7% near GEMSDOE27 | Research only; NO upload |
| [GEMSDOE36](sites/gemsdoe36.html) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | NO — 97.6% near GEMSDOE27 | Research only; NO upload |

## Why the reported 0.2778 remains unexplained

The GEMSDOE32 archive has 37,654 inside-footprint dots, is a subset of
GEMSDOE31, and removes 2,545 GEMSDOE31-only dots near the mirrored known-fault
catalogue. Pruning redundant mass *might* help the published distance-weighted
metric, but the hidden truth and file-bound receipt are unavailable; causality
is unproved. Organizer staff say the known-fault mask is pixel-exact and new
truth may be within 300 m, so a blanket claim that nearby predictions are free
or always harmful is wrong. [Detailed forensic note](research/why-02778-and-how-to-beat-it-20261028.md).

## Evidence from older runs, not independently replayed here

- AP-1: reported HOLDOUT-DTI **0.0389 [0.0282, 0.0491]**, evaluator
  `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld positive *instances*, versus
  its reported control 0.0992. Its saved dots independently overlap the
  pinned lattice by **99.72%**; verdict negative.
- H-UDSR EXP-3: reported HOLDOUT-DTI **0.0947 [0.0822, 0.1073]**, same named
  evaluator and 22,232 withheld instances; control 0.0992. A read-only recheck
  finds **99.85%** lattice overlap; verdict negative.
- H-TRACE EXP-2: prior reported HOLDOUT-DTI **0.0893 [0.0737, 0.1052]**, same
  named evaluator and 22,232 withheld instances, below reported control 0.0975;
  sparse and literal overlap gates failed. Neither its training nor holdout was
  rerun in this review.
- H2: seeded pseudo-feature demo, no holdout. A new saved-byte recheck found
  **5,140,874** masked cells inside the mirrored footprint and **99.92%**
  inside-dot overlap with the pinned lattice. [H2 correction](EXECUTIVE_SUMMARY_H2.md).

These are not organizer scores or estimates of a future hidden-test score.

## Four proposed directions

The qualitative [ranked slate](../research/hypotheses.md) considers paired
3DEP drainage offsets, independent GeoDAWN magnetic flight-line stability,
USGS cross-depth conductance contrast and INGENIOUS fluid-chemistry
contrasts. It identifies layers, signatures, mimics, differences and costs.
All are **untested proposals**, not assigned lanes or proven globally novel.
Official sources list free public data, but the actual bytes, footprint coverage,
resolution and use permissions of the particular products remain to be checked.

## Gates and practical blockers

The explicit assigned method paragraph, complete parallel registry, validated
shared feature stack, authenticated organizer sample and independently
comparable frozen holdout are not established. Owner-mirrored core files were
hash-verified in this workspace but a matching hash does not authenticate origin;
`existing_faults.tif` is absent. One registered lattice leaves 6,649 cells
outside its 3-pixel neighborhood: at 37,654 dots a minimum **82.34%** overlap is
unavoidable, exceeding 70%. This conditional bound does not rule out every
smaller candidate and must not be gamed by moving dots into holes.

A future run needs an assigned lane, visible-only catalogue-derived features,
whole-segment buffered holdout, pixel-exact visible-fault masking, per-feature
leakage canaries, same-fold/evaluator comparison, pre-placement and final
literal registry checks, and saved-byte validation against an authenticated
reference. A separate automated selector—not the format validator—must authorize
a weekly slot. The rejected file's bytes are unavailable; the cause of the
reported [0,1] error is unknown.

## Official sources

[Competition description, metric and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) ·
[Organizer mask clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) ·
[Prize rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) ·
[USGS GeoDAWN](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) ·
[USGS 3DEP](https://www.usgs.gov/3d-elevation-program) ·
[USGS conductance maps](https://doi.org/10.5066/P9TWT2LU) ·
[INGENIOUS compilation](https://gdr.openei.org/submissions/1391).
The [DrivenData Terms](https://www.drivendata.org/termsofuse/) prohibit
automated website monitoring; the site now updates GitHub heads only and links
to the official leaderboard rather than fetching it on a schedule.
