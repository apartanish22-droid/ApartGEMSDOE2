# Executive Summary — Consolidated GEMS / ApartGEMSDOE2 Decision

**Updated 2026-10-28 (H-TRACE session).** This is the single canonical decision
document. It supersedes every lane page, prior release text, and the H2 fractal
pages corrected the same day (`docs/EXECUTIVE_SUMMARY_H2.md`,
`docs/data/run_card_h2.json`, `assets/SUBMISSION_STATUS.txt`).

## Decision at a glance

> **OK to download as research artifacts: yes (links below).**
> **OK to submit to DrivenData this week: NO — for every file in this repository.**
> No candidate has passed the pre-registered holdout **and** uniqueness gates.
> A format/range pass is never submission authorization.

A new unique TIF **was generated this session** (H-TRACE EXP-2, real competition
features, new method, byte-unique SHA-256, finite [0,1]). It **failed** its
holdout and final-dot uniqueness gates, so the honest label is
`negative / RESEARCH ONLY / DO NOT SUBMIT`. Negative results are deliverables;
spending a weekly slot on a gated failure would lower P(win).

## Exactly what file to download, estimated score, and uniqueness

"Estimated score" for the hidden leaderboard is **null for every file**: there is
no calibrated mapping from catalogue hide-and-recover or SGMC diagnostics to the
expert-hidden test set, and writing a projection as a score is prohibited. The
only numeric columns below are labelled **HOLDOUT-DTI** (local evaluator,
22,232 withheld positives) or **user-reported** claims (not organizer receipts).

| File (research download) | HOLDOUT-DTI / claim | Hidden-board estimate | Unique vs the 500-raster registry? | OK to submit |
|---|---|---|---|---|
| `docs/downloads/apartgemsdoe2-trace-exp-2-trace-t1-22438dots-20261028T063240Z-71a21036-zeros.tif` (+ `.zip`, `-nan.tif`) — **this session, H-TRACE** | HOLDOUT-DTI **0.0893** [0.0737, 0.1052] | null (not estimable) | Surface yes (max \|ρ\| 0.1293); **final dots NO** — 86.26% vs a sparse sibling raster, 79.45% vs AP2, both > 70% | **NO** |
| `docs/downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif` (H-UDSR EXP-3) | HOLDOUT-DTI 0.0947 [0.0822, 0.1073] | null | Sparse subset yes; **literal all-registry NO** (99.85% vs lattice) | **NO** |
| AP2 OOFCTRL (bytes identical to GEMSDOE28 D2.8) | HOLDOUT-DTI 0.1060 | null | **NO** (deduplicated champion bytes) | **NO** |
| AP-1 `apartgemsdoe2-ap1-*-37654dots-*` | HOLDOUT-DTI 0.0389 | null | **NO** (99.72% lattice) | **NO** |
| H2 `gems-h2-fractal-faultzone-*` (PR #20 demo) | **null** — seeded pseudo-features, no competition data | null; earlier "0.28–0.32" figure **withdrawn** | Not measured | **NO** |
| Historical site bests (GEMSDOE24–36) | user-reported 0.2449–0.2778 | — | n/a (archival bytes, resubmission out of scope) | **NO** (not independently scored here) |

## What this session ran (3 experiments, pre-registered)

Lane **H-TRACE**: oriented (8 orientations) 1.5 km + 3.1 km trace-coherence gate
on the leak-free H-UDSR Dual-Cover OOF posterior, shared exact-gain axial-crest
emitter outside a 2 px catalogue collar. Measured on the shared
`GEMSDOE32-HIDE-RECOVER-v3.0` evaluator against a fold-honest D28_B2 control
(0.0992):

| Experiment | HOLDOUT-DTI [95% CI] | Paired Δ vs control | SGMC diagnostic | Dots | Worst sparse 3-px overlap |
|---|---|---|---|---|---|
| EXP-1 CTRL-T0 (posterior alone) | 0.0975 [0.0828, 0.1122] | — | 0.0431 | 23,845 | 83.46% |
| EXP-2 TRACE-T1 (gate) | 0.0893 [0.0737, 0.1052] | −0.0082 [−0.0112, −0.0051] | 0.0390 | 22,438 | 86.26% |
| EXP-3 TRACE-T2 (hysteresis) | 0.0898 [0.0740, 0.1061] | −0.0077 [−0.0110, −0.0046] | 0.0390 | 22,353 | 86.33% |

**Conclusion:** on this posterior, km-scale line-coherence gating significantly
*hurts* both holdout proxies, and every supervised-posterior emission converges
onto the same near-catalogue dot attractor as siblings (79–86% overlap). Gates:
G1 format PASS · G2 holdout FAIL · G3 leakage canary PASS (max AUC 0.5733) ·
G4 uniqueness FAIL (sparse + literal). Verdict: **negative**.

## Why 0.2778 leads, and what beating it requires

Full PhD-level analysis with official citations:
`docs/research/why-02778-and-how-to-beat-it-20261028.md`. Short version:
GEMSDOE32 B2 is byte-verified as `(D2.8 ∧ d_catalogue > 2 px)` — 37,654 binary
dots just outside the catalogue, ~50/50 between 0.2–1.5 km and > 1.5 km bands.
Under the distance-weighted Tversky metric (α = 0.2), a dot breaks even if it
earns ≈ 5.6% of one hidden-pixel credit at DTI = 0.2778, so near-catalogue
lineament coverage is cheap and effective. Beating it requires *new detections*
(off-catalogue structures experts actually drew), precision at fixed budget, and
lateral placement inside ±200 m — not more catalogue-halo dots.

## How to submit (only if a future candidate passes every gate)

1. Single-band float32 GeoTIFF, EPSG:32611, shape 3730×3292, transform
   origin (243350, 4508550), 100 m cells; values in [0,1]; outside the test
   footprint null/NaN per the official format text. Or a zip containing exactly
   one such GeoTIFF.
2. Validate the **saved bytes** (`scripts/check_submission.py <file>
   --strict-finite`, `scripts/validate_submission.py`): whole-array range [0,1],
   no NaN inside the footprint — this addresses the portal error
   "Predicted values must be in range [0, 1]" for the `-zeros` variant; the
   `-nan` variant matches the official outside-footprint text. Portal acceptance
   of either is **not** proven (the rejected file's bytes are unavailable).
3. Use the candidate's unique filename stem and its ≤ 140-char note from the
   run card as the portal description. Record the submission-page receipt;
   until then every score is HOLDOUT-DTI or user-reported, never confirmed.

For the current artifact the recorded name/note are:
`apartgemsdoe2-trace-exp-2-trace-t1-22438dots-20261028T063240Z-71a21036-zeros` /
"ApartGEMSDOE2 H-TRACE EXP-2: oriented 1.5/3.1km trace-coherence gate on
DualCover OOF posterior, 22438 dots B2" — recorded for provenance; **do not use**.

## Limitations

Hidden test labels are expert-drawn and undisclosed; organizers explicitly
decline to describe their sources/types/coverage. The grid template here comes
from an owner mirror, not an authenticated organizer download. Two of 500
registry rasters are malformed, so uniqueness audits cover 498. The literal
≤ 70% lattice rule is geometrically unsatisfiable above 22,163 dots; it is
reported literally, never relabelled as passed.
