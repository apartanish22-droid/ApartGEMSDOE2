# H2 fractal artifact — withdrawn; do not submit

> **DECISION: DO NOT DOWNLOAD OR SUBMIT THIS ARTIFACT.** It is a seeded synthetic demonstration, not a geological prediction. The prior upload recommendation, score projection, and uniqueness claim are withdrawn. No leaderboard-score estimate is available.

This page replaces the superseded H2 summary. The former text remains available in Git history for audit; it is not current guidance. See [the current executive summary](EXECUTIVE_SUMMARY.md), [the H2 correction record](data/run_card_h2.json), and [irregularity IR-TRACE-02](../evidence/irregularities_trace_20261028.json).

## What the archived file is

- **Artifact:** `gems-h2-fractal-faultzone-20261028T054632Z-8c5870c5.tif` (also stored under `assets/` for historical provenance).
- **SHA-256:** `5a6da02c45e8cc96399763c1eba4f95bddd781f0ff2223c9d9a7f1dc3e90a801`.
- The saved bytes were read back in this repository review: one-band float32 GeoTIFF; 3730 × 3292; EPSG:32611; transform `(100, 0, 243350, 0, -100, 4508550)`; all 12,279,160 cells finite with values in `[0,1]`; 61,396 nonzero cells. These are **file-format statistics only**, not a score or geological result.
- The artifact was generated in `DEMO MODE` from seeded pseudo-features because no competition feature/label inputs were available. Its code defined every grid cell as footprint, whereas the owner-mirror manifest records 5,167,373 footprint cells. The owner mirror is not organizer-authenticated. Thus the demo does **not** establish official footprint/mask compliance or portal acceptance.
- **HOLDOUT-DTI:** not computed. Withheld-positive count and 95% confidence interval: not available. Leakage canary: not run. Complete-registry uniqueness: not established. New-file leaderboard estimate: not estimable.

## Method implementation audit

The old title claimed multi-scale box-counting fractal dimension and directional complexity anisotropy. The saved generator does not substantiate that claim: `build_h2_map()` uses a multi-scale Gaussian/Sobel gradient magnitude and does not call its box-counting or anisotropy functions; the anisotropy function itself takes the same square neighbourhood for each azimuth. The synthetic demo therefore cannot be treated as a validated implementation of the proposed geology.

The legacy command-line generator is now disabled before it can write an artifact. Do not re-enable it as a submission path. A future real-data H2 experiment would need a newly specified lane, the authenticated data/template, a correct implementation, the shared holdout/evaluator and writer, individual-feature leakage canaries, full pre-placement and final-dot registry checks, and saved-byte validation. Only a separate selector could then consider a weekly slot.

## Current status

**No H2 file is approved for submission. No new H2 TIFF is offered here for download.** The independent nine-site scorecard and the reason GEMSDOE32's reported 0.2778 may be higher are in the [main review](EXECUTIVE_REVIEW.md) and [metric analysis](research/why-02778-and-how-to-beat-it-20261028.md). The 0.2778 association itself remains **USER-REPORTED / UNVERIFIED**; it is not an organizer receipt or an estimate for this artifact.
