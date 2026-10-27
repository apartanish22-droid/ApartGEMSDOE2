---
layout: default
title: ApartGEMSDOE2 — GEMS competition submission
---

# ApartGEMSDOE2 — GEMS competition submission

**DOE GEMS fault-prospectivity competition** (DrivenData competition 306).
This site publishes the project's submission pipeline, an executive summary of
the highest-scoring GEMSDOE results, and a downloadable candidate GeoTIFF.

---

## 📥 Download submission file (click to download)

**File:** [`artifacts/candidate_submission.tif`](artifacts/candidate_submission.tif)

| Item | Value |
|------|-------|
| **Submission name** | `gemsdoe-multi-evidence-prospectivity-v1` |
| **Note** (≤140 chars) | Unique multi-evidence geothermal prospectivity (mag-persistence × K/eTh-gradient × topo-residual, catalogue-masked). Pipeline demo; footprint match unverified. |
| **Format** | Single-band Float32 GeoTIFF, CRS EPSG:32611 |
| **Values** | Finite, no NaN/Inf, all in **[0, 1]** |
| **SHA-256** | `54acf71ab5768f06b74428e7f87a6cd55fe18247d05c73ebd312e1c370ded2a0` |

### ⚠️ Is it OK to download and submit?

**NOT OK TO SUBMIT — do not upload this file to the competition yet.**

| Release-gate check | Result |
|--------------------|--------|
| Opens and reads back as GeoTIFF | ✅ Pass |
| Single band | ✅ Pass |
| All values finite, no NaN / Inf | ✅ Pass |
| All values in **[0, 1]** (fixes `"Predicted values must be in range [0, 1]"`) | ✅ Pass |
| CRS / shape / geotransform match official `sample_submission.tif` | ❌ **UNVERIFIED** |

**Blocker:** the official `sample_submission.tif` (which defines the required CRS, shape, and geotransform) is behind the DrivenData login and is **not present in this repository**. This candidate was therefore built on an illustrative grid and cannot be confirmed to match the official submission footprint.

### How to make it OK TO SUBMIT

1. On a machine with DrivenData access, download `sample_submission.tif` into `data/` (do **not** commit credentials).
2. Re-run `python scripts/generate_submission.py --match data/sample_submission.tif` so the output grid is re-projected/re-sampled to the **exact** official shape, transform, and CRS.
3. Run `python scripts/validate_submission.py artifacts/candidate_submission.tif --sample data/sample_submission.tif --json artifacts/validator-report.json`.
4. Only when every gate prints `true` / `GATE_PASS: true` should you upload the file with the submission name and note above, using a weekly submission slot.

See the full [Executive Summary](executive-summary.md) for the GEMSDOE site comparison, the GEMSDOE32 analysis, sources, limitations, and the machine-readable run card.

---

**Scientific integrity:** no score here is represented as a measured result. All GEMSDOE figures below are user-reported and unverified; none are HOLDOUT-DTI or ORGANIZER-CONFIRMED.
