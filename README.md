# ApartGEMSDOE2 — GEMS fault-prospectivity research

> **Start here every session.** Read this README, the [standing prompt](docs/research/standing-prompt-ap2.md), and [`docs/EXECUTIVE_REVIEW.md`](docs/EXECUTIVE_REVIEW.md) before proposing experiments or preparing a submission. Keep the work auditable and evidence-led; never represent an estimate as a measured score.

## Decision (2026-10-27 AP2 session)

- 🟡 **DOWNLOAD: YES — a new, format-valid file is ready:** [`docs/downloads/apartgemsdoe2-ap2-oofctrl-44090dots-20261027T220804Z-5e265df9-zeros.tif`](docs/downloads/apartgemsdoe2-ap2-oofctrl-44090dots-20261027T220804Z-5e265df9-zeros.tif) (SHA-256 `edf60fd492cc18b835abee8cb7479825f47cd1077aa8609de37f1d9de5ccf50e`, 44,090 dots, 0 on-catalogue). Tracking name `ApartGEMSDOE2-AP2-OOFCTRL-EDF60FD4`; portal note in [`evidence/ap2_run_card.json`](evidence/ap2_run_card.json).
- 🔴 **AUTO-PROMOTE: NO — run-card verdict is `negative`.** It beats the champion-recipe control on HOLDOUT-DTI point estimate (0.1060 [0.0907, 0.1219] vs 0.0992 [0.0860, 0.1127], evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld), but the paired 95% CI on the difference is [−0.0015, +0.0152] (P(Δ>0)=93.9%), and 74.5% of its dots sit within 3 px of one *unscored* Arena8a research raster. **It is unique vs every scored submission in the brief** (worst 56.7% ≤70%, worst |ρ| 0.349 ≤0.90). Spending a slot is an explicit selector decision; this session used **0 slots**.
- The promoted format is the strict `-zeros` file (all 12,279,160 cells finite in [0,1]); do not submit the `-nan` twin. Steps: site → `how-to-submit.html`. Live site (GitHub Pages): https://apartanish22-droid.github.io/ApartGEMSDOE2/

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

The AP2 session vendored the pinned GEMSDOE32 shared tools (`src/gems32/`, see `registry/PROVENANCE.md`), restored the hash-verified competition data, rebuilt the 35-channel feature stack, and ran the preregistered 3 experiments ([`docs/research/ap2-preregistration-20261027.md`](docs/research/ap2-preregistration-20261027.md); corrections in [`docs/research/ap2-pass2-amendment-20261027.md`](docs/research/ap2-pass2-amendment-20261027.md)). Machine-readable evidence lives in `evidence/` (canary, OOF AUCs, experiments, Focus-9 byte forensics, final run card). The emitted candidate (decision banner above) is the EXP3-selected **EXP1 OOFCTRL** field at 44,090 dots — the chain-corroboration arm (AP2-H1's novel mechanism) **lost** on both holdout metrics and was not applied to the final field. The site under `docs/` is generated from that evidence by `scripts/build_site.py`.

Reproduce (needs ~10 GB scratch; expected ≈ 15 min without the broad-registry check):

```bash
pip install -r requirements.txt
export GEMS_DATA_DIR=$PWD/.cache/gems_data GEMS_WORK_DIR=$PWD/.cache/gems_work   # git-ignored
python scripts/restore_data.py
python scripts/build_features.py
python scripts/run_ap2.py --refs-dir /path/to/focus-repo-clones
python scripts/finalize_ap2.py --refs-dir /path/to/focus-repo-clones --broad-registry
python scripts/validate_submission.py docs/downloads/*-zeros.tif
python scripts/build_site.py
python -m unittest discover -s tests -v
```

## Data and source references

Competition data is behind the DrivenData login according to the project request. Do not place credentials in this repository. The supplied public references are listed in the review document; availability and file contents must be checked in an environment with access before they are treated as verified inputs.

## Project values

Maximize P(Win). Own the outcome. Treat each measured result—positive or negative—as evidence that improves the next decision.
