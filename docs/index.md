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

**File:** [`../assets/submission.tif`](../assets/submission.tif)
(also archived as `../assets/gems-h1-radiometric-curvature-convergence-20261027T212405Z-59a3c88e.tif`)

| Item | Value |
|------|-------|
| **Submission name** | `gems-h1-radiometric-curvature-convergence-20261027T212405Z-59a3c88e.tif` |
| **Note** (≤140 chars) | Unique H1 radiometric anomaly x DEM curvature-convergence propensity; not a copy of any prior GEMSDOE site submission. |
| **Format** | Single-band Float32 GeoTIFF, CRS EPSG:32611 |
| **Shape** | 1200 × 1200 (synthetic demo grid) |
| **Values** | Finite, no NaN/Inf, all in **[0, 1]** (min 0.0, max ~0.9847) |
| **SHA-256** | `250d2a554fd0c54c58437c9b724d80aef83173527a3b3bed5b6347b8e76b2d6e` |
| **Status file** | [`../assets/SUBMISSION_STATUS.txt`](../assets/SUBMISSION_STATUS.txt) |

### ⚠️ Is it OK to download and submit?

**NOT OK TO SUBMIT — do not upload this file to the competition yet.**

| Release-gate check | Result |
|--------------------|--------|
| Opens and reads back as GeoTIFF | ✅ Pass |
| Single band | ✅ Pass |
| All values finite, no NaN / Inf | ✅ Pass |
| All values in **[0, 1]** (fixes `"Predicted values must be in range [0, 1]"`) | ✅ Pass |
| CRS / shape / geotransform match official `sample_submission.tif` | ❌ **UNVERIFIED** |

**Blocker:** this is a format demonstration on a synthetic demo grid (1200 × 1200, 100 m). It will NOT match the real submission CRS/shape/geotransform. The official `sample_submission.tif` is behind the DrivenData login and is not in this repository.

**How to reach OK TO SUBMIT:** on a machine with DrivenData access, run
`bash scripts/download_competition_data.sh` to place
`data/numeric_features.tif`, `data/labels.tif`, `data/example_submission.tif` in the repo,
then `python scripts/prepare_data.py`, then
`python src/generate_submission.py` (real-data mode) and
`python src/validate_submission.py ../assets/submission.tif data/grid_reference.json`.
Upload only when every gate passes.

See the full [Executive Summary](EXECUTIVE_SUMMARY.md) for the GEMSDOE site comparison,
the GEMSDOE32 analysis, candidate hypotheses, sources, limitations, and the machine-readable run
card.

---

**Scientific integrity:** no score here is represented as a measured result. All GEMSDOE figures
are user-reported and unverified; none are HOLDOUT-DTI or ORGANIZER-CONFIRMED.
