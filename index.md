---
layout: default
title: ApartGEMSDOE2 — GEMS competition submission
---

# ApartGEMSDOE2 — GEMS fault-prospectivity submission

**DOE GEMS fault-prospectivity competition** (DrivenData competition 306).
Reproducible workflow for identifying previously unmapped, geothermally relevant faults and
producing a competition-format GeoTIFF only after it passes automated validation gates.

---

## 📥 Download submission file (one click)

**File:** [`artifacts/candidate_submission.tif`](artifacts/candidate_submission.tif)

| Item | Value |
|------|-------|
| **Submission name** | `gemsdoe-multi-evidence-prospectivity-v1` |
| **Note** (≤ 140 chars) | Unique multi-evidence geothermal prospectivity (mag-persistence × K/eTh-gradient × topo-residual, catalogue-masked). Pipeline demo; footprint match unverified. |
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

**Blocker:** the official `sample_submission.tif` (defines the required CRS, shape, geotransform)
is behind the DrivenData login and is not in this repository, so the footprint match cannot be
verified.

**How to reach OK TO SUBMIT:** on a machine with DrivenData access, download
`sample_submission.tif` into `data/`, then run
`python scripts/generate_submission.py --match data/sample_submission.tif` and
`python scripts/validate_submission.py artifacts/candidate_submission.tif --sample data/sample_submission.tif`.
Upload only when every gate passes.

---

## 📊 Executive summary — GEMSDOE24/25/27/28/30/31/32/33/36

See the full [Executive Summary](docs/executive-summary.md).

GEMSDOE32 has the highest *user-reported* score in the list (0.2778, `h33-h33-2-b2-…-zeros`), but
it is **USER-REPORTED, UNVERIFIED**, and its raster/uniqueness are unavailable. **None of the
listed submissions can be recommended for upload on the current evidence.** Our candidate is a
distinct generation method but is not yet certifiable (footprint match unverified; no holdout
labels available).

---

**Scientific integrity:** no score here is represented as a measured result. All GEMSDOE figures
are user-reported and unverified; none are HOLDOUT-DTI or ORGANIZER-CONFIRMED.
