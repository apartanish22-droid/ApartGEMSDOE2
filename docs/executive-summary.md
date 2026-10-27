---
layout: default
title: Executive summary — GEMS competition submission pipeline
---

# Executive summary — GEMS competition submission pipeline

**Repository:** [apartanish22-droid/ApartGEMSDOE2](https://github.com/apartanish22-droid/ApartGEMSDOE2)
**Competition:** DOE GEMS — Geothermal Exploration & Mapping (DrivenData competition 306)
**Landing page:** [index.md](index.md) · **Submission file:** [`artifacts/candidate_submission.tif`](artifacts/candidate_submission.tif)

> **Read first.** This page is an executive index, not a measured result. No competition data
> (`training_features.tif`, `labels.tif`, `sample_submission.tif`, registry rasters) is present in
> this checkout — it is behind the DrivenData login. Consequently **no score here is HOLDOUT-DTI or
> ORGANIZER-CONFIRMED**. Every GEMSDOE figure below is **USER-REPORTED, UNVERIFIED** (transcribed
> from the task prompt). A projection is never written as a score.

---

## 1. Download the submission file (obvious, one click)

**File:** [`artifacts/candidate_submission.tif`](artifacts/candidate_submission.tif)

| Item | Value |
|------|-------|
| Submission name | `gemsdoe-multi-evidence-prospectivity-v1` |
| Note (≤ 140 chars) | Unique multi-evidence geothermal prospectivity (mag-persistence × K/eTh-gradient × topo-residual, catalogue-masked). Pipeline demo; footprint match unverified. |
| Format | Single-band Float32 GeoTIFF |
| CRS | EPSG:32611 (UTM zone 11N) — https://epsg.io/32611 |
| Shape | 300 × 300 (illustrative grid; see blocker below) |
| Values | Finite, no NaN/Inf, all in **[0, 1]** |
| SHA-256 | `54acf71ab5768f06b74428e7f87a6cd55fe18247d05c73ebd312e1c370ded2a0` |
| Machine-readable validator report | [`artifacts/run-card.json`](artifacts/run-card.json) |

### Is it OK to download and submit?

**NO — NOT OK TO SUBMIT.** Do not upload this file to the competition yet.

| Release-gate check (README.md) | Result |
|---|---|
| Opens and reads back as GeoTIFF | ✅ Pass |
| Single band | ✅ Pass |
| All values finite, no NaN / Inf | ✅ Pass |
| All values in **[0, 1]** — avoids `"Predicted values must be in range [0, 1]"` | ✅ Pass |
| CRS / shape / geotransform match official `sample_submission.tif` | ❌ **UNVERIFIED — BLOCKER** |

**Blocker:** `sample_submission.tif` (the source of truth for CRS/shape/geotransform) is behind the
DrivenData login and is not in this repository. The candidate was therefore built on an
illustrative EPSG:32611 grid and cannot be confirmed to match the official footprint.

**How to reach OK TO SUBMIT:** on a machine with DrivenData access, download
`sample_submission.tif` into `data/` (no credentials in this repo), then run
`python scripts/generate_submission.py --match data/sample_submission.tif` and
`python scripts/validate_submission.py artifacts/candidate_submission.tif --sample data/sample_submission.tif`.
Only when every gate prints `true` / `GATE_PASS: true` should you upload with the name/note above
using a weekly submission slot.

---

## 2. GEMSDOE site comparison — highest reported submissions

The nine sites in scope: **GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36**.
“Best reported” = highest score shown for that site in the task prompt. **Not verified.**
Pixelwise uniqueness is **UNKNOWN** for every row because registry rasters and the candidate TIFFs
are not available in this checkout. Distinct filenames/methods do **not** establish distinct raster
contents.

### Ranking by highest user-reported score (descending)

| Rank | Site | Best reported submission (file to download) | Reported score | Score status | Unique vs other GEMSDOE sites? | Submit decision |
|:---:|---|---|---|---|---|---|
| 1 | [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | **0.2778** | USER-REPORTED, UNVERIFIED | UNKNOWN | **Do not submit** |
| 2 | [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | **0.2750** | USER-REPORTED, UNVERIFIED | UNKNOWN | **Do not submit** |
| 3 | [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | **0.2710** | USER-REPORTED, UNVERIFIED | UNKNOWN | **Do not submit** |
| 4 | [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan` | **0.2708** | USER-REPORTED, UNVERIFIED | UNKNOWN | **Do not submit** |
| 5 | [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | **0.2632** | USER-REPORTED, UNVERIFIED | UNKNOWN | **Do not submit** |
| 6 | [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | **0.2600** | USER-REPORTED, UNVERIFIED | UNKNOWN | **Do not submit** |
| 6 | [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | **0.2600** | USER-REPORTED, UNVERIFIED | UNKNOWN | **Do not submit** |
| 8 | [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | **0.2477** | USER-REPORTED, UNVERIFIED | UNKNOWN | **Do not submit** |
| 9 | [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | **0.2449** | USER-REPORTED, UNVERIFIED | UNKNOWN | **Do not submit** |
| — | **This repo (candidate)** | [`artifacts/candidate_submission.tif`](artifacts/candidate_submission.tif) | **—** (not estimable) | Projection only, not a score | Distinct generation method; pixelwise uniqueness UNKNOWN | **NOT OK TO SUBMIT yet** |

### Which is the best submission to submit?

On the evidence available right now: **none can be recommended.** GEMSDOE32 has the highest
*user-reported* score (0.2778), but it is unverified, its raster and method card are unavailable,
and its uniqueness is unknown. Submitting any of these files would be an unverified guess. The
responsible action is to (a) recover the competition data, (b) run the leakage canary and
segment-buffered holdout evaluation, (c) beat the current comparable HOLDOUT-DTI best, and (d)
only then use a weekly submission slot.

---

## 3. GEMSDOE32 deep-dive — `h33-h33-2-b2-…-zeros`: 0.2778

**Why and how did it get the highest score?** Cannot be determined from the information available.
The filename suggests a particular experimental family and a “zeros” output convention, but a
filename alone does not establish the algorithm, why it worked, or whether it was leakage-free.
No method card, source code, input raster, holdout definition, score receipt, or comparison raster
is present in this checkout or on the linked page. A PhD-level causal explanation would be
speculation.

**Irregularity flagged for review:** a submission whose name ends in `-zeros` scoring 0.2778 is
anomalous under the project's pooled DTI metric (α = 0.2, β = 0.8, Tversky-style). An all-zeros
prediction gives TP = 0, FN = all positives, FP = 0 → DTI = 0, not 0.2778. Plausible explanations:
(a) “zeros” means zeros only outside the footprint with real values inside; (b) labels inverted;
(c) the score is misreported or refers to a different evaluator version; (d) a leaderboard quirk.
This must be resolved before treating 0.2778 as a credible benchmark.

**Can we generate a submission that scores higher than 0.2778?** Possible in principle, but not
demonstrable here. “Higher than 0.2778” can be claimed only after a comparable, leakage-resistant
holdout experiment or an organizer receipt. The prompt's conflicting leaderboard context (0.3195
and 0.4413) is unresolved and is not used as an estimate or verified standing.

---

## 4. Novel candidate hypothesis (this repo's submission)

### Method lane (unique, not copied from any listed GEMSDOE site)

Blind, geothermally active faults in the northern Great Basin should be highlighted where **three
independent evidence channels coincide**:

1. **Multi-scale aeromagnetic edge persistence** — a susceptibility contrast that persists across
   smoothing scales is more likely to be a fault offset of magnetic basement than one-scale noise.
   (Distinct from GEMSDOE30's single-scale edge and from plain ridge magnitude.)
2. **K/eTh radiometric alteration gradient** — hydrothermal alteration / lithologic juxtaposition
   along concealed structures, not raw radiometric intensity. (Distinct from GEMSDOE46's raw
   channel fusion.)
3. **Topographic residual lineament** — DEM curvature/terrain position after removing broad
   regional relief; subtle scarps not expressed as mapped ridges.

Final prospectivity = `clip(magnetic_persistence × alteration_gradient × topographic_residual, 0, 1)`,
then **zeroed on known USGS/INGENIOUS catalogue traces** (pixel-exact) so the raster emphasises
**off-catalogue (previously unmapped) structures** — exactly what the competition rewards.

### Why it could catch faults missing from the catalogue

Catalogued faults are mapped surface traces. A buried or blind fault may express itself as a
magnetic basement offset, an alteration (K/eTh) gradient, and a subtle topographic residual
*without* appearing as a mapped surface fault. Multiplying independent channels suppresses
single-sensor noise, and catalogue-masking removes known traces so the score is driven by new
structures.

### How it differs from anything already implemented here

This checkout previously contained only documentation — no feature stack, no evaluator, no writer,
no candidate TIFF. The listed GEMSDOE methods are dominated by dotted-ridge, topographic-gap,
Poisson-dot, PINN, and scatter approaches. The triple-evidence masked product above is a distinct
generation method. Distinct method ≠ proven distinct raster: pixelwise uniqueness requires the
registry rasters, which are unavailable.

---

## 5. Candidate hypotheses not yet tried (ranked)

| Priority | Hypothesis | Layer(s) & signature | Why it could catch uncatalogued faults | Difference vs repo / listed sites | Est. DTI | Cost |
|:---|---|---|---|---|---|---|
| 1 | Multi-scale magnetic persistence × K/eTh gradient × topo residual, catalogue-masked **(this submission)** | Airborne magnetic gradients at 2 scales; K/eTh gradient; DEM residual; catalogue mask | Buried fault = coincident susceptibility + alteration + subtle scarp, absent from surface catalogue | Distinct triple product + pixel-exact catalogue mask; not in listed GEMSDOE results | — (untested) | Low–medium |
| 2 | Local-field-normalized magnetic boundary | Magnetic total-field gradient ÷ local field amplitude (normalizes for regional field) | A sharp susceptibility boundary marks a buried structure; normalization suppresses regional-field artifacts that mimic faults | Different from raw edge magnitude (GEMSDOE30); novelty not established | — | Medium |
| 3 | Radiometric K/eTh & eU/eTh alteration-gradient concordance | K, eTh, eU channels; ratio gradients; spatial concordance of two independent ratios | Hydrothermal alteration juxtaposes lithologies along concealed structures; concordance suppresses single-channel noise | Radiometric fusion appears in listed results (GEMSDOE46); needs a specified concordance statistic to be novel | — | Medium |
| 4 | Scale-selective topographic residual lineament | DEM curvature / topographic position residual after removing broad relief | Buried/subtle fault → weak scale-dependent geomorphic expression absent from inventory | Topographic/scarp methods extensively represented; high duplication risk | — | Medium–high |

No winner is selected here. Per the protocol, at most three experiments, holdout validation before
any weekly slot, and the lane/selector step are separate. None of these has been holdout-validated
in this checkout, so all remain **research questions, not approved experiments**.

---

## 6. Validation results for the candidate TIF

Machine-readable report: [`artifacts/run-card.json`](artifacts/run-card.json)

| Check | Value |
|---|---|
| File | `artifacts/candidate_submission.tif` |
| SHA-256 | `54acf71ab5768f06b74428e7f87a6cd55fe18247d05c73ebd312e1c370ded2a0` |
| Single band / dtype | ✅ 1 band / float32 |
| CRS | EPSG:32611 |
| Shape | 300 × 300 (illustrative) |
| Finite / no NaN / no Inf | ✅ / ✅ / ✅ |
| Values in [0, 1] | ✅ (min 0.0, max ~0.344) |
| Matches sample CRS/shape/transform | ❌ UNVERIFIED (sample unavailable) |
| Gate pass | ❌ False |
| Verdict | **negative** — do not submit until footprint match is verified |

---

## 7. Sources (for manual review)

These links were supplied in the task and should be treated as leads, not independently verified
evidence, unless fetched:

- [DrivenData competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData competition about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [Competition rules / landing page](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Competition data page (login required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Competition leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDawn survey](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [Submission guidance PDF (NLR)](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS OpenEI submission](https://gdr.openei.org/submissions/1391)
- [EPSG:32611](https://epsg.io/32611)
- [Tversky index](https://en.wikipedia.org/wiki/Tversky_index)

---

## 8. Run card (machine-readable)

```json
{
  "created_utc": "2026-10-27T21:20:47.354798+00:00",
  "hypothesis": "Coincident multi-scale magnetic edge persistence x K/eTh radiometric alteration gradient x topographic residual lineament, catalogue-masked to emphasise off-catalogue blind geothermal faults.",
  "mechanism": "Multiply three independent normalised evidence layers; zero on known catalogue traces so only unmapped structures remain; values clipped to [0,1].",
  "named_non_fault_mimic": "Non-tectonic lithologic contacts, surficial cover, and non-fault topographic edges can mimic linear magnetic/radiometric contrast.",
  "holdout_dti": null,
  "holdout_ci_95": null,
  "evaluator_version": null,
  "withheld_positive_count": null,
  "correlation_overlap_vs_registry": "UNTESTED \u2014 registry rasters unavailable in this checkout.",
  "raster_sha256": "54acf71ab5768f06b74428e7f87a6cd55fe18247d05c73ebd312e1c370ded2a0",
  "validator_output": {
    "file": "artifacts/candidate_submission.tif",
    "sha256": "54acf71ab5768f06b74428e7f87a6cd55fe18247d05c73ebd312e1c370ded2a0",
    "opens_and_reads_back": true,
    "single_band": true,
    "dtype": "float32",
    "crs": "EPSG:32611",
    "shape": [300, 300],
    "transform": [400.0, 0.0, 220000.0, 0.0, -133.33333333333334, 4420000.0],
    "finite": true,
    "no_nan": true,
    "no_inf": true,
    "values_in_0_1": true,
    "min": 0.0,
    "max": 0.34373828768730164,
    "matches_sample_crs_shape_transform": "UNVERIFIED \u2014 sample_submission.tif unavailable (DrivenData login required)",
    "sample_path": null,
    "gate_pass": false,
    "failures": [
      "CRS/shape/transform do not match official sample_submission.tif (or sample unavailable)"
    ]
  },
  "submission_name": "gemsdoe-multi-evidence-prospectivity-v1",
  "submission_note": "Unique multi-evidence geothermal prospectivity (mag-persistence x K/eTh-gradient x topo-residual, catalogue-masked). Pipeline demo; footprint match unverified.",
  "verdict": "negative",
  "ok_to_submit": false,
  "submit_blocker": "Cannot verify match to official sample_submission.tif CRS/shape/geotransform (competition data behind DrivenData login)."
}
```

---

## 9. Limitations & next steps

1. **Data blocker.** Competition data is behind the DrivenData login; this checkout cannot download
   `training_features.tif`, `labels.tif`, `sample_submission.tif`, `existing_faults.tif`, or registry
   rasters. Obtain them on an authenticated machine into `data/` and re-run the pipeline.
2. **No holdout / no score.** Without `labels.tif` and a spatial holdout evaluator, no holdout DTI,
   confidence interval, or score estimate can be produced. All GEMSDOE figures are user-reported
   and unverified.
3. **Uniqueness unknown.** Pixelwise uniqueness vs registry rasters cannot be tested without the
   registry rasters and the other candidate TIFFs.
4. **Weekly-slot discipline.** Do not spend a submission slot until a candidate beats the current
   comparable HOLDOUT-DTI best (with 95% CI) and passes the full release gate. Promotion is a
   separate selector step within the weekly cap.
5. **Next session:** restore the shared cached feature stack and canonical
   `evaluate_holdout.py` / `submission_writer.py`; resolve the single method-paragraph lane;
   run the leakage canary (AUC > 0.90 ⇒ presumed leakage); then execute up to three experiments.

---

*Generated by scripts/generate_submission.py and scripts/validate_submission.py. See README.md for the full operating charter.*
