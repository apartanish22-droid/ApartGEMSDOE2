# ApartGEMSDOE2 — GEMS fault-prospectivity research

> **Start here every session.** Read this README and [`docs/EXECUTIVE_REVIEW.md`](docs/EXECUTIVE_REVIEW.md) before proposing experiments or preparing a submission. Keep the work auditable and evidence-led; never represent an estimate as a measured score.

## Mission and operating charter

Build a reproducible, scientifically defensible workflow for identifying previously unmapped faults relevant to geothermal exploration in the GEMS competition, evaluating it without spatial leakage, and producing a competition-format GeoTIFF only after it passes the project's validation gates. The objective is to improve the probability of a strong competition result—not to maximize the number of experiments or submissions.

Core working principles:

- **Maximize P(Win):** prioritize robust spatial holdout performance, reproducibility, and compliance over speculative leaderboard claims.
- **Own the outcome:** report failures, blockers, and negative results; fix shared tooling in its canonical location rather than maintaining private forks.
- **Scientific integrity:** distinguish reported leaderboard values, organizer-confirmed receipts, holdout results, and projections. Cite sources and label uncertainty.
- **No leakage:** hide whole fault segments with a buffer; derive catalogue-dependent features only from visible faults; mask visible faults pixel-exactly; test individual features for leakage before using them.
- **No unauthorized selection:** do not use a weekly submission slot until the candidate beats the current spatial-holdout best and passes validation. The protocol's separate selector step makes the final promotion decision.
- **No false deliverables:** do not create a synthetic or placeholder TIFF and call it a submission. A submission is download-ready only after the correct data, transform, footprint, finite values, `[0,1]` range, and uniqueness checks have all passed.

## Required experimental protocol

1. Follow the session's explicitly assigned scientific-method lane. Before surface placement and again on the final dots, compare the raster with every available registry raster: stop and record a duplicate if rank-correlation is greater than `0.90` or more than `70%` of dots lie within `3` pixels of a registry raster's dots.
2. Reuse the project's cached feature stack and canonical `evaluate_holdout.py` / `submission_writer.py` (or their established equivalents). Do not fork shared tools. The holdout is hide-and-recover by fault segment plus buffer; pool DTI using `alpha=0.2`, `beta=0.8`, and a `300 m` triangular kernel.
3. Run the leakage canary for each feature alone. An AUC above `0.90` is presumed leakage until investigated and explained.
4. Label every score as either **HOLDOUT-DTI** (include evaluator version, withheld-positive count, and 95% CI) or **ORGANIZER-CONFIRMED** (transcribe from a submission receipt). Never label an estimate or projection as a score.
5. Stop at the assigned experiment/time budget. Record a JSON run card with hypothesis, mechanism, a plausible non-fault mimic, holdout DTI and CI, registry correlation/overlap, raster SHA-256, validator output (finite values within footprint, `[0,1]`, CRS/shape/transform), submission name, a note no longer than 140 characters, and `promote` / `negative` verdict.

## Submission release gate

A downloadable `.tif` may be marked **OK TO SUBMIT** only when it is a single-band GeoTIFF and automated checks confirm the official sample-submission footprint, CRS, shape, and geotransform; no NaN/Inf within the footprint; all predicted values are in `[0,1]`; the output opens and reads back; its SHA-256 and method provenance are recorded; and the registry correlation/dot-overlap checks pass. The downloadable file should be accompanied by a unique submission name and a concise note. A valid TIFF is not evidence of a high score, and a score projection is not an official result.

## Current repository state

This checkout contains documentation, a static decision page, and a read-only format validator with synthetic tests. It does **not** contain the feature stack, labels, sample-submission raster, registry rasters, cached feature stack, holdout evaluator, submission writer, dataset downloader, or an existing candidate TIFF. Consequently, no holdout experiment, raster-level uniqueness test, score estimate, or valid competition TIFF can be produced from this checkout alone. The work and blockers are itemized in [`docs/EXECUTIVE_REVIEW.md`](docs/EXECUTIVE_REVIEW.md). Do not infer that a TIFF exists just because the desired workflow is described here.

## Data and source references

Competition data is behind the DrivenData login according to the project request. Do not place credentials in this repository. The supplied public references are listed in the review document; availability and file contents must be checked in an environment with access before they are treated as verified inputs.

## Project values

Maximize P(Win). Own the outcome. Treat each measured result—positive or negative—as evidence that improves the next decision.

## Automated format check and site

The static [submission decision page](docs/index.html) puts the no-submit status first. To run the read-only format validator after obtaining the **official** sample and a genuine candidate:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements-validation.txt
.venv/bin/python scripts/validate_tif.py data/sample_submission.tif data/candidate.tif
.venv/bin/python -m unittest discover -s tests -v
```

The validator intentionally returns `submission_authorized: false` even if `format_valid: true`: it cannot certify geology, holdout performance, or uniqueness. No TIFF can currently be generated responsibly from this documentation-only checkout. GitHub Pages must be configured to serve `/docs` on the default branch after merge; the HTML page itself does not deploy the site.
