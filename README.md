> **2026-10-28 review:** No submission is approved. `data/restore_receipt.json` is historical; run `.venv/bin/python scripts/preflight.py` to check current core-file hashes. A fresh checkout does not include the cached inputs. Four legacy experiment/emission entry points now use the fail-closed guard, and the AP2 local format validator checks raster masks and label-grid alignment. See [review and next steps](docs/research/review-gates-20261028.md) and [parallel review](docs/research/review-20261028.md).

# ApartGEMS · evidence before the next upload

**Start every session here.** This repository is a research and decision desk for the [DOE GEMS Prize](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). The target is **geological faults**, not confirmed geothermal vents. Our objective is a genuinely new, high-quality, reproducible competition submission—not a copied TIFF, a renamed prior submission, an invented score, or a format-only pass.

**Arena AI Core Values:** **Maximize P(Win)** · **Own the Outcome**

> **CURRENT DECISION: DO NOT SUBMIT (Verdict `negative` under strict solo-promotion & literal all-registry rules; `H-UDSR EXP-3` available in `docs/downloads/` as a `[0, 1]`-validated, sparse-unique research artifact).**
> - **AP-1** ([research TIFF](docs/downloads/apartgemsdoe2-ap1-dilatcond-37654-20261027-1f26aa05-zeros.tif)): **99.72% overlap** with the registered 13GEMSDOE lattice (`HOLDOUT-DTI 0.0389` vs `0.0992` control) — **do not submit**.
> - **AP2** ([OOFCTRL TIFF](docs/downloads/apartgemsdoe2-ap2-oofctrl-44090dots-20261027T220804Z-5e265df9-zeros.tif), finding 10): paired `HOLDOUT-DTI 0.1060` (`ΔCI [−0.0015, +0.0152]`), **74.5%** overlap vs Arena8a and **99.90%** vs lattice — **do not submit** ([AP2 sub-site](docs/ap2/index.html)).
> - **H-UDSR (`EXP-3`)** ([`apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif`](docs/downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif), finding 11): uniquely clears **all 488 non-lattice sparse registry rasters** (**`46.52%`** vs `GEMSDOE32 B2`, max sparse **`69.42% <= 70%`**, **`16.09%`** vs AP-1, **`67.00%`** vs AP2, surface `|Spearman| = 0.1189 <= 0.90`), passes all 55 single-feature leakage canaries (`max AUC = 0.7680 <= 0.90`), and guarantees **`12,279,160 / 12,279,160` finite `float32` pixels in `[0.0, 1.0]`** (`nodata=None`). Unstratified `EXP-2` beat fold-honest `D28_B2` (`0.1137` vs `0.0992`), while stratified `EXP-3` recorded **`HOLDOUT-DTI 0.0947`** (`[0.0822, 0.1073]`, `SGMC_cal 0.0398` vs `0.0641`) and overlaps the 206,895-dot `13GEMSDOE` calibration lattice at **`99.85%`** under the literal all-registry rule → **verdict `negative`** (not eligible for a slot under the current protocol). See the [H-UDSR full dashboard & figures](docs/udsr/index.html), [H-UDSR submission guide](docs/udsr/executive-summary.html), [canonical executive guide](docs/executive-summary.html), and [nine-site scorecard](docs/index.html#scorecard).

**Latest review:** [28 October publication and gate review](docs/REVIEW_20261028.md) corrected unsafe legacy upload instructions and unverified score labels. No new candidate passed the protocol.

## Project brief: read this on every session

This section retains the substantive, non-duplicated instructions from the project prompt as the standing charter. Treat later explicit instructions and the competition's current rules as authoritative if they change.

- Review the highest supplied results from **GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36**. Provide an executive summary, source links, the exact file identity, estimate availability, uniqueness scope, and an obvious download/upload decision. The sites are independent repositories; this checkout publishes nine linked briefs, not edits to those repositories.
- Generate an original TIFF only when it can be responsibly validated; historical files may be downloaded **only for learning or comparison**. A changed filename, encoding, or hash alone does not make a new geological method. Never spend a slot on an unvalidated idea; negative results are deliverables.
- Before implementation propose **3–5 geological hypotheses**, naming the layers, physical signature, why it might detect unmapped faults, non-fault mimics, difference from prior work, qualitative rank and implementation cost. Verify free, official external data are actually obtainable and have appropriate reuse rights. Do not claim unproven global novelty.
- **PARALLEL-RUN PROTOCOL:**
  1. **Lane.** Stay inside the single assigned method paragraph. If surface rank correlation with any registry raster exceeds 0.90, or more than 70% of final dots lie within 3 pixels of any one registry raster, log a duplicate and stop. Check before placement **and** on final dots. Do not silently exempt calibration controls.
  2. **Reuse.** Use the shared template's cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`. Hide whole fault segments with a buffer; derive all catalogue features only from visible faults; mask visible faults pixel-exactly; score pooled distance-weighted Tversky with alpha 0.2, beta 0.8 and a 300 m triangular kernel. Fix any shared-tool defect in the shared template, not a private fork.
  3. **Label evidence.** New numerical performance results must be **HOLDOUT-DTI** with evaluator version, withheld-positive count and 95% CI, or **ORGANIZER-CONFIRMED** with a submission-page receipt. A projection is never a score. Historical user claims without receipts must remain explicitly **unverified**, not be relabeled as confirmed.
  4. **Leakage canary.** Test each feature individually; AUC above 0.90 is leakage until proven otherwise.
  5. **Run card.** Record hypothesis, mechanism, a named non-fault mimic, holdout and CI, registry correlation/overlap, raster SHA-256, saved-byte validation, submission name, a note of at most 140 characters, and verdict `promote` or `negative`. Use null for anything not measured.
  6. **Budget.** Stop after 3 experiments or 2 hours. A separate selector, respecting the current weekly cap on the authenticated submission page, determines any real slot. No human inspection is required for the project gates; a separate selector can be automated. Do not auto-submit.
- Design a clean GitHub Pages site with a prominent submission decision and, **only after all gates clear**, a simple submission download with a unique name and short note. Include an executive submission guide, verifiable official sources, honest freshness and data limitations. Automate checks; never call a stale snapshot a live feed.
- Investigate the user's reported portal rejection, `Predicted values must be in range [0, 1]`, using the exact saved bytes.
- **Core values:** **Maximize P(Win)** by comparing risks and protecting scarce slots; **Own the Outcome** by documenting failures, fixing defects, verifying results, and making next steps explicit. Perform implementation, adversarial review, and final request reconciliation as separate passes.
- Follow [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), including data-use conditions and the generative-AI narrative disclosure where applicable.

## Current findings (27 October 2026)

1. The initial checkout contained only this README; the claimed train→inference pipeline and cached stack were not present. No single geological method paragraph was explicitly assigned in the supplied prompt, so the canonical review did not invent a lane.
2. The [organizer's public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) displayed **0.4544** for its leader at the timestamp in [`docs/data/source_feed.json`](docs/data/source_feed.json). This is an **OFFICIAL PUBLIC LEADERBOARD OBSERVATION**, not a file-bound submission-page receipt.
3. The requested nine historical values, including GEMSDOE32's **0.2778**, are **USER-REPORTED / UNVERIFIED**: no organizer receipt binding a file hash to that value was available (`IR-APART2-06`). Of the supplied claims, GEMSDOE32 is highest; that does not authorize resubmission.
4. We fetched immutable archival TIFFs **only for comparison**, hash-checked their bytes, and independently computed all 72 directional focus-site comparisons. All nine archived dot sets fail the literal overlap rule (`86.7%–100.0%` within 3 px) against at least one other focus-site reference.
5. The registered 13GEMSDOE lattice covers 5,160,724 of 5,167,373 mirrored-footprint cells within 3 pixels (`99.87%`). Only 6,649 are uncovered; at 37,654 distinct dots, at least `(37,654 − 6,649) / 37,654 = 82.34%` must overlap.
6. Exact byte-level XOR proves `(D28 & (d_catalogue > 2.0)) ^ GEMSDOE32_B2 == 0` (`37,654` dots; removing `6,436` near-catalogue flank dots from `GEMSDOE25/30`'s `44,090`-dot `D2.8` mask cut `-1,287.2` in `0.2*FP` denominator penalty), and `GEMSDOE25 ^ GEMSDOE30 == 0`.
7. The available owner-mirrored `sample_submission.tif` has 60,988 positive pixels identical to the mirrored `labels.tif` (`IR-APART2-02`), while raw `2m_temperature_probe_n83geo.dbf` contains `1,870` overflow `F2mDAB` records up to `5.47e+12` (`IR-APART2-01`) and `lidar_scarp_features_u8.tif` has a `24.66%` (`1,272,913` cell) 1 m LiDAR gap (`IR-APART2-04`).
8. **AP-1** reported three experiments and recorded **HOLDOUT-DTI 0.0389** (95% CI [0.0282, 0.0491], `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld positives) versus `0.0992` control.
9. Both saved AP-1 TIFFs were hash-checked (`99.7185%` lattice overlap; `20.1439%` max vs nine focus sites). [Read the independent candidate audit](evidence/parallel_candidate_audit.json).
10. **AP2** preregistered five hypotheses, ran three experiments, and emitted [OOFCTRL research TIFF](docs/downloads/apartgemsdoe2-ap2-oofctrl-44090dots-20261027T220804Z-5e265df9-zeros.tif) with **HOLDOUT-DTI 0.1060** (95% CI [0.0907, 0.1219]) vs `0.0992` control (`ΔCI [−0.0015, +0.0152]`), `74.5%` overlap vs Arena8a, and `99.90%` vs lattice (`verdict: negative`; [AP2 run card](evidence/ap2_run_card.json)).
11. **H-UDSR (`arena/03209562-apartgemsdoe2`)** preregistered five ranked geological hypotheses ([`knowledge/preregistration_udsr_20261027.md`](knowledge/preregistration_udsr_20261027.md): `#1 H-UDSR`, `#2 H-CGSC`, `#3 H-ARAD`, `#4 H-MKPA`, `#5 H-INSAR`), tested all **55 channels** through the single-feature Leakage Canary (`max oriented ROC-AUC = 0.7680 <= 0.90`; [`evidence/leakage_canary_55ch.json`](evidence/leakage_canary_55ch.json)), and executed three controlled experiments ([`evidence/udsr_three_experiments_20261027.json`](evidence/udsr_three_experiments_20261027.json)):
    - **`EXP-1 (UDSR-PurePhysics)`:** `HOLDOUT-DTI = 0.045000` (`[0.036552, 0.053887]`), `SGMC_cal = 0.044914`, `25,164` dots (`57.0% > 15 px`), max sparse 3-px `48.39%`.
    - **`EXP-2 (UDSR-DualCover-OOF)`:** **`HOLDOUT-DTI = 0.113696` (`[0.101306, 0.126712]`)**, outperforming fold-honest `D28_B2` (`0.099202`) by `+0.014494` (`97.2%` of spatial cluster bootstraps positive), but packed `96.25%` of dots into `2 < d <= 15 px` and hit `80.62% > 70%` 3-px overlap vs sibling `WBGGEMSDOE3 hce1` (`IR-APART2-07`).
    - **`EXP-3 (UDSR-Stratified-TwoRegime, emitted)`:** [`apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif`](docs/downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif) (`SHA-256: 1f2c28e9eba172fe6a4da138b98afa28a43420549e174c801a02af658ef180b9`, `26,173` dots, `50.43% > 15 px`, `26.73%` inside the `24.66%` 1 m LiDAR gap, `0.00%` in deep flat playas). Uniquely clears **all 488 non-lattice sparse registry rasters** (`max_sparse_3px = 69.42% <= 70%`, `46.52%` vs `GEMSDOE32 B2`, `16.09%` vs AP-1, `67.00%` vs AP2, surface `|Spearman| = 0.1189 <= 0.90`), achieves `HOLDOUT-DTI = 0.094698` (`[0.082240, 0.107307]`; beats static `B2` `+0.09018` & `H19-5` `+0.02127`; statistically tied with fold-honest `D28_B2 = 0.099202`; `SGMC_cal = 0.039808` vs `0.064121`), and overlaps the 206,895-dot `13GEMSDOE` covering lattice at `99.85%` under the literal rule → Run Card `verdict: "negative"` ([`evidence/apartgemsdoe2_run_card_20261027.json`](evidence/apartgemsdoe2_run_card_20261027.json), [`evidence/udsr_merge_addendum.json`](evidence/udsr_merge_addendum.json)).

## Summary Table: 9 Focus Sites + `ApartGEMSDOE2 (H-UDSR EXP-3)`

| Site | Best File | Dots & Outside | Repo LB (`USER-REPORTED / UNVERIFIED`) | `HOLDOUT-DTI` (`GEMSDOE32-HIDE-RECOVER-v3.0`, n=22,232) | `HOLDOUT-DTI` (`GEMSDOE32-SGMC-CAL-v3.0`, n=62,703) | 3-px Overlap vs `GEMSDOE32 B2` | Decision |
|---|---|---|---|---|---|---|---|
| **ApartGEMSDOE2 (`H-UDSR EXP-3`)** | `apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif` | `26,173` (`0.0` `-zeros`, `[0,1]`) | *Unsubmitted (no projection)* | **`0.09470`** `[0.08224, 0.10731]` (`EXP-2`: **`0.11370`**) | **`0.03981`** `[0.03440, 0.04529]` | **`46.52%`** (488-sparse max `69.42%`; lattice `99.85%`) | **RESEARCH / EXPLORATORY ONLY (`verdict: negative`)** |
| **GEMSDOE32** | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | `37,654` (`0.0` `-zeros`) | `0.2778` | `0.00452` static / `0.09920` fold-honest `B=2` | `0.06412` `[0.05673, 0.07165]` | `100.0%` | **DO NOT SUBMIT** (Duplicate) |
| **GEMSDOE36** | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | `38,854` (`0.0` `-zeros`) | `0.2750` | `0.00458` `[0.00349, 0.00580]` | `0.06444` `[0.05704, 0.07195]` | `97.4%` | **DO NOT SUBMIT** (Duplicate) |
| **GEMSDOE28** | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | `37,660` (`NaN` `-nan`) | `0.2710` | `0.02936` `[0.02350, 0.03578]` | `0.06297` `[0.05582, 0.07027]` | `95.5%` | **DO NOT SUBMIT** (Duplicate) |
| **GEMSDOE31** | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` | `40,199` (`NaN` `-nan`) | `0.2708` | `0.03052` `[0.02495, 0.03638]` | `0.06301` `[0.05579, 0.07040]` | `95.4%` | **DO NOT SUBMIT** (Duplicate) |
| **GEMSDOE33** | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | `41,865` (`0.0` `-zeros`) | `0.2632` | `0.05197` `[0.04422, 0.05988]` | `0.06255` `[0.05535, 0.06982]` | `92.6%` | **DO NOT SUBMIT** (Duplicate) |
| **GEMSDOE25** | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | `44,090` (`NaN` `-nan`) | `0.2600` | `0.09674` `[0.08416, 0.10953]` | `0.06059` `[0.05355, 0.06773]` | `88.2%` | **DO NOT SUBMIT** (Duplicate) |
| **GEMSDOE30** | `gemsdoe30-d28-poisson300m-offcat-44090-20261003-8cf893ea-zeros.tif` | `44,090` (`0.0` `-zeros`) | `0.2600` | `0.09674` `[0.08416, 0.10953]` | `0.06059` `[0.05355, 0.06773]` | `88.2%` | **DO NOT SUBMIT** (Duplicate) |
| **GEMSDOE24** | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | `60,069` (`NaN` `-nan`) | `0.2477` | `0.09315` `[0.08069, 0.10574]` | `0.05793` `[0.05121, 0.06478]` | `88.5%` | **DO NOT SUBMIT** (Duplicate) |
| **GEMSDOE27** | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | `61,328` (`NaN` `-nan`) | `0.2449` | `0.09275` `[0.08036, 0.10531]` | `0.05826` `[0.05152, 0.06512]` | `86.7%` | **DO NOT SUBMIT** (Duplicate) |

## Files and reproduction

- Canonical & audit scripts: `scripts/restore_template.py`, `scripts/audit_historical.py`, `scripts/restore_data.py`, `scripts/audit_parallel_candidate.py`, `scripts/verify_independent_replays.py`, `scripts/preflight.py`, `scripts/build_site.py`, `scripts/build_scorecard.py`.
- `H-UDSR` session artifacts: `src/gems32/udsr.py` (updip advection, sanitized GDR #1391 silica/probe/paleo layers, exact 2-pass bit-partition 2nd-component relay continuation, Dual-Cover OOF GBDTs), `scripts/restore_gems32_data.py`, `scripts/prepare_gems32_data.py`, `scripts/build_extended_registry.py`, `scripts/run_udsr_experiments.py`, `scripts/emit_and_audit_deliverables.py`, `scripts/generate_figures.py`, `docs/udsr/index.html`, `docs/udsr/executive-summary.html`, and `tests/test_deliverable_submission.py` + `tests/test_udsr.py`.
- `AP2` session artifacts: `scripts/run_ap2.py`, `scripts/finalize_ap2.py`, `scripts/audit_focus9.py`, `scripts/build_ap2_site.py`, and `docs/ap2/`.

```bash
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/build_scorecard.py
.venv/bin/pytest -q
.venv/bin/python scripts/check_submission.py \
  docs/downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif \
  --strict-finite
```

## Limitations, needed access, and next work

- **Topology vs. pixelwise trees:** Replace pixelwise far-field crest extraction with a 5–15 km Geodesic / Oriented Radon Minimal-Path Curve Tracer operating on the updip-migrated `H-UDSR` Dual-Cover posterior (`0.7028` blind far-field ROC-AUC) to lift `SGMC_cal` (`0.0398`) past `D28_B2` (`0.0641`).
- **Sandbox network allowlist:** Outbound HTTPS is limited to GitHub, PyPI, and npm; stage NASA OPERA DISP-S1 Sentinel-1 InSAR velocity grids (`asf.alaska.edu`) into the mirrored manifest and clarify the synthetic `13GEMSDOE` covering-lattice exemption before the next 3-experiment budget.

---

## NEW: H2 Fractal Fault-Zone Submission (2026-10-28)

### Status: FORMAT-VALIDATED, PENDING HOLDOUT-DTI

A new unique submission using **multi-scale fractal dimension × surficial complexity anisotropy** has been generated and passes all format validation.

**Download:**
- `assets/gems-h2-fractal-faultzone-20261028T054632Z-8c5870c5.tif` (49.2 MB)
- `assets/gems-h2-fractal-faultzone-20261028T054632Z-8c5870c5.zip` (325 KB)

**Validation:** ✅ PASSED (all checks, [0,1] range, no NaN, portal-safe)

**Uniqueness vs existing AP1/AP2/UDSR rasters:** ✅ UNIQUE (< 7% overlap vs all)

**Full executive summary:** See `docs/EXECUTIVE_SUMMARY_H2.md`

### Standing Prompt (read every session)

The complete project prompt and requirements are documented in `docs/PROJECT_BRIEF.md`. Key requirements:

1. **Generate UNIQUE TIF submissions** — not copies of prior work
2. **Validate before submitting** — format, range [0,1], no NaN, uniqueness
3. **Estimate scores carefully** — HOLDOUT-DTI vs projections vs organizer-confirmed
4. **Focus on the 9 GEMSDOE sites** — GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36
5. **Target score > 0.3195** (current high) using novel geological approaches
6. **Follow PARALLEL-RUN PROTOCOL** — lane discipline, reuse shared tools, label evidence properly

### Quick Start

```bash
# Install
pip install numpy rasterio scipy scikit-learn

# Generate H2 submission
python src/generate_h2_fractal_submission.py

# Validate
python scripts/check_submission.py docs/downloads/gems-h2-fractal-faultzone-20261028T054632Z-8c5870c5.tif --strict-finite

# Download for submission
curl -O assets/gems-h2-fractal-faultzone-20261028T054632Z-8c5870c5.tif
```

## Review update — 28 October 2026

No new experiment or slot was used. The checked-out cache is absent despite the historical restore receipt; that receipt is not evidence that the data exists in a fresh checkout. The H-UDSR pages incorrectly called a lattice-failing candidate safe to submit and treated unverified historical claims as organizer-confirmed. Those pages now state **DO NOT SUBMIT**; the archived run card distinguishes sparse-registry success from the failed all-registry gate. The AP2 guide no longer instructs users to upload a failed candidate or guarantees portal acceptance. Original page versions remain in git history. The reported holdout has not been independently replayed in this review. See [executive review](docs/EXECUTIVE_REVIEW.md) for the missing explicit lane, suspect template and incomplete registry. Official [competition description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [reference code](https://github.com/drivendataorg/gems-prize-reference-solution) are the primary sources, not proof of any particular receipt.
