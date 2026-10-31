# Executive summary — GEMS submission decision (31 Oct 2026)

**Verdict: DO NOT UPLOAD ANY FILE.** No file in this repository currently passes every gate the team has set, and the uniqueness gate has a defect that no dense file can pass.

Every number below is labelled with one of:
- **HOLDOUT-DTI** — our own catalogue-proxy evaluation (not the organizer's hidden test), with evaluator version and CI where available.
- **USER-REPORTED** — a score quoted in the brief with no organizer receipt.
- **ORGANIZER-CONFIRMED** — none exists in this repository.

---

## 1. Download table

| File to download | What it is | Estimated score | Unique vs the nine GEMSDOE sites? | OK to submit? |
|---|---|---|---|---|
| [`apartgems-v4-ridge-tmi-isohg-nms-q5pct-20261030.tif`](../docs/downloads/apartgems-v4-ridge-tmi-isohg-nms-q5pct-20261030.tif) (SHA-256 `f6f3e7c9…`) | Label-free TMI + gravity ridge NMS, 203,418 dots, NaN outside footprint | **HOLDOUT-DTI 0.0741** (east half, CI 0.0599–0.0979, 22,196 withheld cells; from its [run card](../evidence/v4_run_card.json)). Not a leaderboard estimate. | **Partly.** Literal lattice overlap 99.83% (**fails**). Max overlap with a non-lattice registry raster 48.5% (passes; repo-reported, not re-run). | **NO** |
| [`apartgemsdoe2-h-ridge3-tensorfuse-37654-20261030-nan.tif`](../docs/downloads/apartgemsdoe2-h-ridge3-tensorfuse-37654-20261030-nan.tif) | H-RIDGE3 catalogue-free ridge fusion, 37,654 dots | **Not estimable.** No holdout run. | **Partly.** Lattice overlap 99.25% (**fails**). | **NO** |
| [`apartgemsdoe2-h-ridge3-tensorfuse-37654-20261030-zeros.tif`](../docs/downloads/apartgemsdoe2-h-ridge3-tensorfuse-37654-20261030-zeros.tif) | Zeros-outside twin of the file above | **Not estimable.** | **Partly.** Lattice 99.25% (**fails**). | **NO** |
| [`apartgemsdoe2-sarpu-exp2-lefm-sarpu-37654dots-20261028T235500Z-25593731-zeros.tif`](../docs/downloads/apartgemsdoe2-sarpu-exp2-lefm-sarpu-37654dots-20261028T235500Z-25593731-zeros.tif) | Highest repo holdout proxy (H-SARPU EXP-2) | **HOLDOUT-DTI 0.113838** (CI 0.09999–0.12708, per [run card](../evidence/sarpu_run_card_20261028.json)). Split is unbuffered (issue #60), so treat as optimistic. | **Partly.** Lattice 99.82% (**fails**). | **NO** (repo verdict: negative, research only) |
| [`apartgemsdoe2-h-blind-conduit-radiometric-magnetic-curvature-25k-20261031T044226Z-c92314e1-zeros.tif`](../docs/downloads/apartgemsdoe2-h-blind-conduit-radiometric-magnetic-curvature-25k-20261031T044226Z-c92314e1-zeros.tif) — **research demo only** | H-BLIND-CONDUIT format demo; coordinate-synthetic fields, not real geophysical rasters | **Not estimable.** No holdout. | **Not established.** 0.00% vs GEMSDOE32 B2 only; not a full registry check. Footprint-mask proxy audit fails. | **NO.** 15,987 / 25,000 positive cells are outside the repository finite-mask proxy; see [independent audit](../evidence/h_blind_conduit_footprint_audit_20261031.json). |
| The nine GEMSDOE site bests (24, 25, 27, 28, 30, 31, 32, 33, 36) | Other sites' published files | **USER-REPORTED** only (e.g. 0.2477–0.2778). No receipt. | **NO.** The repo's nine-site audit ([evidence](../evidence/audit_nine_sites_20261030.json)) finds each one duplicates another site's raster under the literal rule. | **NO** |

**Format caution:** previous run cards report the older candidate grid/range checks against owner-mirrored references; those checks do not establish organizer authentication or portal acceptance. The H-BLIND-CONDUIT builder's receipt counted all 12,279,160 rectangular pixels as footprint because it used an all-finite zeros-outside reference. A separate saved-byte comparison against the repository's 5,167,373-cell NaN-outside footprint proxy found 15,987 of its 25,000 positive cells outside that mask. Do not describe that demo as official-format-valid. See [`evidence/h_blind_conduit_footprint_audit_20261031.json`](../evidence/h_blind_conduit_footprint_audit_20261031.json).

---

## 2. Why nothing is approved: the lattice gate fails for random dots too

The protocol says a file is a duplicate if more than 70% of its dots fall within 3 px of one registry raster's dots. The repo applies that to a 13GEMSDOE calibration lattice (206,895 dots).

I measured it directly (2026-10-31, same definition as `src/gems32/registry_audit.py`):

| Dot set | Share of dots within 3 px of the lattice |
|---|---|
| Lattice's own 3-px coverage of the footprint | **99.87%** |
| Uniform random dots, 34,500 (3 seeds) | 99.86–99.90% |
| Uniform random dots, 37,654 (3 seeds) | 99.83–99.88% |
| Uniform random dots, 203,418 (3 seeds) | 99.87–99.88% |

**Random dots fail the literal 70% gate at every density.** A dense lattice covers almost the entire footprint, so the gate cannot distinguish a designed submission from noise. Under the literal rule, no file in this repo can pass, including the nine site files. This is an **irregularity for owner review**, not a finding about any one candidate.

The repo's README cites a "random null 67.8%" for H-RIDGE3. I could not reproduce it or find its source in `evidence/`; my measurement is ~99.9%. **Flagged for review.**

---

## 3. Leaderboard check (verified 31 Oct 2026)

Fetched from the [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), ranks 1–23:

- #1 **0.4544** (xiaofanhu), #2 **0.3934** (cfld__), #3 **0.3917** (Batik Shirt Brothers).
- **0.4413 and 0.3195 do not appear in ranks 1–23.** The repo's 30 Oct fetch placed 0.3195 at rank #48 (top-50 rows). I did not re-check beyond rank 23 this session.

The brief's claim that 0.3195 is "the highest score right now" is **incorrect**: the top score is 0.4544.

---

## 4. Why GEMSDOE32 (user-reported 0.2778) beat GEMSDOE30 (user-reported 0.2600)

Verified from the registry rasters (`.cache/gems_data/registry_focus/`):

- GEMSDOE32's 37,654 dots are a **strict subset** of GEMSDOE30's 44,090 dots (0 dots added, 6,436 removed).
- The 6,436 removed dots are **not on** any catalogue pixel (0 of 6,436), but **all 6,436 lie 1–3 px from one** (`existing_faults.tif`). Neither file has any dot on a catalogue pixel.

**Scoring rules this depends on (official sources):**
- Organizer staff state that pixels on known USGS/INGENIOUS faults are masked and do not count toward penalty terms. Masking covers only those pixels, not their 300 m halo ([DrivenData forum, 16 Sep, chrisk-dd](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)).
- The metric is DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w), a **recall-weighted** Tversky index with a 300 m triangular kernel ([repo metric, `src/gems32/metric.py`](../src/gems32/metric.py); problem page [competition page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)).

**Mechanism (hypothesis, consistent with those rules):** a dot 1–3 px from a known fault, and not within 300 m of a hidden new fault, adds 0.2 × its kernel weight of false positive. Removing those dots lowers FP_w while losing no true positives, so the score rises. Because α = 0.2, the gain per dot is small, which fits a 0.018 difference. **This is not a measured score.** The hidden new-fault set is not public, so the effect cannot be confirmed without an organizer receipt.

I previously described the metric as precision-weighted. That was wrong. It is recall-weighted, and the correction is recorded here.

**Implication:** a file built the same way from GEMSDOE32 is a near-duplicate. Removing catalogue-halo dots from any other file gives a file that overlaps GEMSDOE32 almost completely, so it fails uniqueness by design.

---

## 5. Irregularities flagged for review

1. **Lattice gate is not discriminative** (section 2). Owner decision needed on a density-aware rule.
2. **"Predicted values must be in range [0, 1]"** cannot be diagnosed. The rejected bytes are not in the repo. Every candidate here is in [0, 1] inside the footprint. The official `sample_submission.tif` uses NaN outside the footprint; the zeros-outside variants are a repo choice the portal has not confirmed. Please send the rejected file if you want it checked.
3. **Uniqueness numbers disagree across docs:** 24.1% (focus 9 sites, README) vs 48.5% (all non-lattice registry rasters, decision table). These use different scopes; both are repo-reported. Not re-run this session.
4. **Format-valid label is wrong for one file:** `apartgemsdoe2-hrm-contrast-blind-geothermal-20261030T015536Z-d6cdf8f8-zeros.tif` has 21,064 of 40,000 dots outside the official footprint ([decision table](../docs/submission-decision.html)).
5. **Holdout split is unbuffered:** 15,705 of 22,232 withheld positives lie within 15 px of visible faults (issue #60). Every HOLDOUT-DTI above is optimistic for that reason.
6. **Scores are unverified:** the 0.2477–0.2778 site scores and the 0.3195 / 0.4413 figures have no organizer receipt.
7. **The organizer data tab requires login.** Training data came from a hash-verified owner mirror, not the organizer. Pins verified this session (`restore_data.py`).

---

## 6. What it would take to submit something

1. Owner decision on the lattice rule (density-calibrated, or remove the lattice).
2. A buffered hide-and-recover holdout (issue #60 fixed) to get an honest HOLDOUT-DTI.
3. A new hypothesis that beats the current holdout best, using one of the candidates in [`knowledge/candidate_slate_20261030.md`](../knowledge/candidate_slate_20261030.md). None has been measured.
4. An organizer receipt for any score reported as a leaderboard result.

Until then: **do not upload.**

---

## Run card (JSON)

```json
{
  "date_utc": "2026-10-31",
  "hypothesis": "No file in the repo is a valid submission under the literal uniqueness rule; the lattice gate is non-discriminative.",
  "mechanism": "13GEMSDOE lattice covers 99.87% of the footprint within 3 px; any dot set, including uniform random dots, scores 99.8-99.9% against it.",
  "named_non_fault_process_that_could_mimic_signal": "Dense uniform placement (any space-filling dot pattern) would also score high on the overlap gate.",
  "holdout_dti": {
    "v4_candidate": {"value": 0.07412, "ci95": [0.05987, 0.09793], "label": "HOLDOUT-DTI", "n_withheld": 22196, "evaluator": "src/gems32/metric.py, east half"},
    "sarpu_exp2": {"value": 0.113838, "ci95": [0.09999, 0.12708], "label": "HOLDOUT-DTI", "caveat": "unbuffered split, issue #60"}
  },
  "correlation_overlap_vs_registry": {"lattice_within_3px_candidates": [0.9983, 0.9925, 0.9925, 0.9985, 0.9982], "random_null_within_3px": [0.99870, 0.99855, 0.99896, 0.99878, 0.99862, 0.99825, 0.99868, 0.99879, 0.99875]},
  "raster_sha256": {
    "v4": "f6f3e7c98de4323b3bc4981648170c5afa361fda4eac03313c08fcaf1b51b8d6",
    "ridge3_nan": "9ef2450c48ce72d65be7e0f7bbf021e4e838a17ca71f1c8067f91353a976ce82",
    "ridge3_zeros": "2031ebd623f0bfe9c0566c3c346362f8915330669d0ab9933c460537181051bf",
    "sarpu_exp2_zeros": "030153b3bd16fb04eef1afa95f8931f27cd132e645c6825309e197cd3a85aa82"
  },
  "validator_output": "All files: EPSG:32611, 3730x3292, transform matches sample, float32, finite inside footprint, values in [0,1]. Outside: NaN or zeros by file.",
  "submission_name": "none",
  "submission_note": "none (do not upload)",
  "verdict": "negative"
}
```

*Sources:* [competition problem and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) · [submission rules (NLR PDF)](https://docs.nlr.gov/docs/fy26osti/96647.pdf) · [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) · [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [DOE INGENIOUS dataset (OpenEI)](https://gdr.openei.org/submissions/1391) · [EPSG:32611](https://epsg.io/32611)
