# ApartGEMSDOE2 — GEMS fault-prospectivity research

> **Start here every session.** Read this README, [`docs/EXECUTIVE_SUMMARY.md`](docs/EXECUTIVE_SUMMARY.md) and [`knowledge/preregistration-20261027.md`](knowledge/preregistration-20261027.md) before proposing experiments or preparing a submission. Keep the work auditable and evidence-led; never represent an estimate as a measured score.
>
> **Current decision (2026-10-27): 🔴 DO NOT SUBMIT any file.** New unique AP-1 GeoTIFF is downloadable for research (`docs/downloads/apartgemsdoe2-ap1-dilatcond-37654-20261027-1f26aa05-zeros.tif`) but verdict **negative** (HOLDOUT-DTI 0.0389 vs champion 0.0992). Site: `docs/index.html`. Original full brief (retained verbatim as charter): [`docs/EXECUTIVE_REVIEW.md`](docs/EXECUTIVE_REVIEW.md) §“Sources” + session prompt; the 0.3195/0.4413 leaderboard figures there are stale (live #1 0.4544, fetched 2026-10-27).

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

## Current repository state (2026-10-27)

Implemented and verified: vendored canonical metric/holdout/emission/writer (`src/gems32/`, `src/gemsdoe32/`, `PROVENANCE.md`; metric tests 8/8 pass), data restorer (`scripts/restore_data.py`, SHA-pinned mirrors in `registry/`), AP-1 lane (`src/apart/`, pre-registered), 3-experiment budget spent (EXP-1 screen, EXP-2 OOF, EXP-3 confirmation), unique research GeoTIFF + validator receipts (`docs/downloads/`, `evidence/`), GitHub Pages site (`docs/index.html`).

**Lane (single, frozen):** AP-1 dilatational-stepover conductivity coincidence — see `knowledge/preregistration-20261027.md`. Next viable lane is AP-2 (Euler depth clusters, in-band, no external data). Do not re-run AP-1 variants without a new pre-registration.

Reproduce: `pip install -r requirements.txt` → `python scripts/restore_data.py --target-dir /tmp/gems_data` → `GEMS_DATA_DIR=/tmp/gems_data python scripts/run_experiment_oof.py --variant strain2 --order smooth --tag exp2` → `python scripts/build_final.py` → `GEMS_DATA_DIR=/tmp/gems_data python scripts/check_submission.py docs/downloads/apartgemsdoe2-ap1-dilatcond-37654-20261027-1f26aa05-zeros.tif --strict-finite`.

**Limitations / blockers:** (1) all nine historical scores are OWNER-REPORTED (no organizer receipts) — treat as claims; (2) no validated HOLDOUT-DTI→leaderboard transfer, so no leaderboard estimate is quoted; (3) DrivenData originals remain login-walled (mirrors are integrity-pinned, not organizer-authenticated); (4) CPU-only sandbox (3.8 GB RAM) — no GPU U-Net training attempted; (5) weekly slot promotion is a separate selector step, not taken.

## Data and source references

Official: [problem/metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), [EPSG:32611](https://epsg.io/32611), [Tversky index](https://en.wikipedia.org/wiki/Tversky_index), [NLR guidance PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [GDR #1391](https://gdr.openei.org/submissions/1391). Do not place credentials in this repository.

## Project values

Maximize P(Win). Own the outcome. Treat each measured result—positive or negative—as evidence that improves the next decision.

> Merge note (2026-10-27): parallel H1 demo (`assets/…59a3c88e.tif`, synthetic 1200×1200 grid, no holdout, NOT OK) remains in-tree for provenance and is superseded by the measured AP-1 decision above. Do not submit either candidate.
