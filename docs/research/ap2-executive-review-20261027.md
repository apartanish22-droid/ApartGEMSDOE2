# Executive review: GEMSDOE24/25/27/28/30/31/32/33/36 — byte-measured rerun (2026-10-27)

> **Merge-integration addendum (supersedes the submit wording below): DO NOT SUBMIT.** After this session, main's integrated decision applied the all-registry novelty rule literally: the AP2 candidate has 99.9% of dots within 3 px of the registered 5-px calibration lattice (`evidence/ap2_merge_addendum.json`), in addition to the negative paired-CI and Arena8a gates. The file below remains the research download of record; no slot was or is authorised.


> This supersedes the earlier documentation-only review, which correctly refused to infer
> anything from filenames when no rasters were present. Everything below was re-measured
> in the AP2 session from the actual TIFF bytes of the nine cloned focus repos
> (`scripts/audit_focus9.py` → `evidence/ap2_focus9_forensics.json`; clone HEADs pinned in
> `registry/PROVENANCE.md`). Live scores remain **OWNER-REPORTED**: no repo stores a
> DrivenData receipt binding a score to these bytes.

## Decision

| Question | Answer |
|---|---|
| Which single file should be downloaded from this repo? | `docs/downloads/apartgemsdoe2-ap2-oofctrl-44090dots-20261027T220804Z-5e265df9-zeros.tif`, SHA-256 `edf60fd492cc18b835abee8cb7479825f47cd1077aa8609de37f1d9de5ccf50e` |
| Is it safe for the portal format gate? | **Yes.** Saved-byte validator PASS: single-band float32, EPSG:32611, 3730×3292, template transform, all 12,279,160 cells finite in [0,1], 0 dots on catalogue. |
| Is it unique vs all listed GEMSDOE submissions? | **Yes vs every scored winner** (worst 56.7% of dots within 3 px, worst surface \|ρ\| 0.349, no subset/identical relation). **No** under the stricter broad-registry rule: 74.5% vs one *unscored* Arena8a research raster. |
| Estimated score | HOLDOUT-DTI (`GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld) **0.1060 [0.0907, 0.1219]** vs champion-recipe control 0.0992 [0.0860, 0.1127]. PROJECTION (not a score) 0.2846–0.2970. Paired Δ CI [−0.0015, +0.0152], P(Δ>0)=93.9%. |
| OK to submit? | **Selector decision required** — preregistered run-card verdict is `negative` (G2 paired-CI and G3b broad-uniqueness fail). This session used **0 weekly slots**. |
| Should any of the nine historical files be (re)submitted? | **No.** They are one measured family (below) and already have owner-reported scores. |

## The nine winners, measured

| Site | Best-listed file (measured bytes) | OWNER-REPORTED | Dots | sha256[:8] | AP2 dots ≤3 px | AP2 surface ρ |
|---|---|---:|---:|---|---:|---:|
| GEMSDOE32 | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | 0.2778 | 37,654 | c55bafc4 | 52.7% | 0.301 |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-...-zeros.tif` | 0.2750 | 38,854 | e1589102 | 52.9% | 0.296 |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif` | 0.2710 | 37,660 | 7c74270a | 53.7% | 0.315 |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif` | 0.2708 | 40,199 | acd85393 | 54.1% | 0.318 |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | 0.2632 | 41,865 | 87f857d5 | 54.7% | 0.326 |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif` | 0.2600 | 44,090 | 3e78737f | 55.0% | 0.340 |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | 0.2600 | 44,090 | 8cf893ea | 55.0% | 0.340 |
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif` | 0.2477 | 60,069 | 3e0730e8 | 56.4% | 0.349 |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif` | 0.2449 | 61,328 | a9bf76b5 | 56.7% | 0.347 |

Exact dot-set relations measured (not inferred from names): **25 ≡ 30** (identical dot
masks in different byte encodings); **24 ⊂ 27**; **31 ⊂ 25/30**; **32 (champion) ⊂ 25/30,
31, 36**. The nine are therefore repeated measurements of one H19-5 backbone under
progressive deletion, not nine independent methods.

## Why the GEMSDOE32 champion scored 0.2778

The champion is four deletions, not a new detector: H19-5 dense 121,131 px (0.1922) →
thin to 60,069 (0.2477) → 44,090 (0.2600) → delete dots ≤1 px (100 m) from the catalogue
→ 40,199 (0.2708) → delete ≤2 px → 37,654 (0.2778); all scores OWNER-REPORTED. Under
DTI = TPw/(TPw + 0.2·FPw + 0.8·FNw) with a 300 m triangular kernel, the thinning kept
75.9% of kernel credit while removing 63.6% of false-positive mass, and the B=2 step
removed 2,545 dots whose measured credit (≈0.002–0.016/dot) sat far below the
marginal break-even α·DTI ≈ 0.0556. Predictions on or beside mapped faults can only add
FP mass (the private test faults are off-catalogue), so each documented deletion
monotonically raised DTI. Full derivation in the preregistration §0.

**Can it be beaten?** Unproven. AP2 is better on hide-and-recover point estimate
(+6.9% relative) but worse off-catalogue on SGMC (0.0583 vs 0.0641 calibrated), and the
paired CI straddles zero. The official public leaderboard read directly this session
stands at **0.4544** (xiaofanhu) — the earlier prompt values 0.3195 and 0.4413 were stale
snapshots. That gap is a modelling-capacity gap (GPU segmentation), not something dot
post-processing on the same ridges has ever closed under this evaluator. Only an
organiser receipt can settle >0.2778.

## Hypotheses and experiments (3, preregistered)

Five ranked hypotheses were written before code (`docs/research/ap2-preregistration-20261027.md`):

| # | Hypothesis (layers) | Signature / transform | Gain / cost | Outcome |
|---|---|---|---|---|
| 1 | AP2-H1 CCCB: OOF HistGB on the 35-ch stack (core + LiDAR/radiometric externals) × along-axis chain vote; credit-bar budget. Experts trace continuous lineaments; speckles are the champion's FP load. Chain had existed only as channels, never as gate×posterior. | Chain = max over 4 axes of top-decile support ±5 px; field ×(0.6+0.4·chain), gate ≥0.2 | High / medium | **Tested; chain rejected, CTRL emitted** |
| 2 | AP2-H2 blind-basin reallocation (LiDAR-valid, potential fields; SGMC only for prevalence). Gap basins hold faults pre-LiDAR mapping missed; prior work used a fixed gap quota. | Budget split by measured off-catalogue prevalence (≈1.61× gap) | Medium / medium | Deferred (one lane) |
| 3 | AP2-H3 dip-migrated basement step (depth-to-basement, gravity, RTP). Buried-fault edges sit updip of the trace by the kernel width; prior dip use was an additive arm only. | Basinward depth-scaled crest shift ≤2 px | Medium / low–medium | Deferred (one lane) |
| 4 | AP2-H4 SGMC/Qfaults difference gated by ≥2 coincident edges. Targets newer compilations; solo ≈0.05 upstream and SGMC-as-input breaks the SGMC evaluator. | Corroborated off-catalogue traces | Low (measured) / low | Rejected |
| 5 | AP2-H5 seismicity-chain lineaments (bands 10/16; USGS ComCat FDSN named but egress-blocked here). Blind faults may host microseismicity; band solo AUC 0.55–0.57. | Hough/Radon collinearity of density ridges | Low / high (blocked) | Rejected |

Executed lane: recover the OOF multi-physics stack (PU LiDAR-gap weighting) and test
chain corroboration + a credit-bar budget scan. Results (`evidence/ap2_experiments.json`):
canary PASS (worst `curv_s2` AUC 0.584); OOF quadrant AUC 0.620–0.750; EXP1 CTRL
0.1046 vs EXP2 CHAIN 0.1035 (chain also worse on SGMC-cal, 0.0535 vs 0.0570) → **chain
mechanism rejected**; EXP3 selected CTRL @44,090 (0.1060). The evaluator was verified
bit-exactly against upstream's published control (D28 visible-only B=2 → 0.09920232315251679).
Two first-run implementation bugs (censorship-biased control, `min_sep=2.8` saturation)
were found in Pass 2, amended openly, and the flawed receipts retained
(`evidence/ap2_*flawed_v1*.json`, `docs/research/ap2-pass2-amendment-20261027.md`).

## Remaining limitations / next work

1. No ORGANIZER-CONFIRMED score exists for any file in this family — fetch and pin
   receipts before treating 0.2778 (or any projection) as measured.
2. The binding uniqueness constraint is now the *unscored* modern registry (Arena8a/H47/
   H48 share the same GBM+crest ridges; even the chain mask overlaps Arena8a 77.4%).
   A genuinely orthogonal field needs label-free physics channels that move secondary
   ridges, or potential-field-only modelling — not another GBM variant.
3. A GPU is required for the obvious next modelling step (Tversky-loss segmentation);
   this sandbox has 2 vCPU / 3.8 GB RAM and GitHub/PyPI-only egress (AP2-H5 seismicity
   via USGS ComCat FDSN remains data-blocked here).
4. Do not re-tune variants against the same holdout until the CI clears zero — that is
   gate-shopping; the protocol's 3-experiment budget exists to prevent it.

## Run card

`evidence/ap2_run_card.json` (verdict `negative`; gates G1 ✓, G2 ✗, G3 ✓, G3b ✗, G4 ✓,
G5 ✓, G6 ✓; raster sha256, validator output, submission name
`ApartGEMSDOE2-AP2-OOFCTRL-EDF60FD4`, 97-character note, weekly slots used: 0).
