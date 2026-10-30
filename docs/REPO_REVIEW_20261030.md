# Repository review — 30 October 2026

## Executive decision

**Do not upload any repository TIFF.** The current decision remains negative: there is no candidate whose score, requested buffered-segment holdout, full-registry uniqueness and organizer-format acceptance have all been established. The existing executive summary and run cards document the reasons. This review generated no candidate, made no score projection, and used no competition submission slot.

## Review passes

### Pass 1 — implementation and repo state

- Confirmed the checkout is on `arena/5b84bcb0-apartgemsdoe2` and the working tree was initially clean.
- Read the root `README.md` as the standing project brief and inspected the current executive summary, research/review decision and run-card/status artifacts.
- Confirmed the repo already records the supplied nine-site historical comparison and explicitly labels the reported 0.2778 as unverified, the hidden-test estimate as unavailable, and existing TIFFs as research-only. No new TIFF was made because the gates in the brief remain unmet.
- Checked the validation dependency file. It lacked `pytest`, `scipy`, `scikit-learn`, and `pandas`, which are needed by the test suite and fail-closed script tests. Consequently, the documented minimal validation environment could not run tests as intended.

### Pass 2 — dependency fix and verification

Updated `requirements-validation.txt` to install the minimal project test/runtime set: NumPy, SciPy, Rasterio, pytest, scikit-learn and pandas. Created an ignored local virtual environment and installed from this file. The first run, before adding the model dependencies, exposed four missing imports and then two fail-closed checks masked by absent pandas; after updating the dependency list, the complete suite passed: **183 passed, 9 skipped, 4 subtests passed**. There were 65 Rasterio `PendingDeprecationWarning` warnings; these did not fail tests.

### Pass 3 — original-request and risk re-check

- Rechecked that no current evidence supports a submit-ready candidate or a defensible new-file score estimate. Therefore the download action must remain unavailable/clearly prohibited, not inferred from format-only validation.
- The historical leaderboard figures are source/user reports, not authenticated submission receipts; they cannot establish which exact binary received a score or that a new candidate will outperform it.
- The strict duplicate gate and missing authenticated template/valid holdout remain blockers. Neither filenames nor hashes establish scientific uniqueness.
- No external competition data were downloaded; this sandbox has no DrivenData authentication. No slot was selected, and there is no organizer-confirmed score.

## Changes

- `requirements-validation.txt`: added the packages required to run this repository's current test suite successfully.
- This review document records what was checked and what remains unverified.

## Next work, in priority order

1. Resolve the requested protocol's blockers: authenticate the official submission template and dataset, get a complete pinned registry, and obtain a corrected shared evaluator/writer plus buffered whole-segment holdout that recomputes catalogue features from visible faults only.
2. Re-establish the frozen current-best under that same protocol; run per-feature leakage canaries and pre-placement as well as post-placement full-registry novelty checks. Respect the three-experiment/two-hour cap and separate slot selector.
3. Only promote if the paired uncertainty interval beats the matched baseline, every release gate passes, and the exact saved TIFF passes byte-level validator checks. Otherwise publish a negative run card.
4. Keep score evidence labeled either **HOLDOUT-DTI** with evaluator/version, withheld-positive count and CI, or **ORGANIZER-CONFIRMED** copied from a file-bound organizer receipt. Do not present projections as scores.

## Source and evidence boundary

This is a repository-state and local-test review. Historical URLs and claims are linked from [`README.md`](../README.md), [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md), and the linked evidence files. This review did not independently fetch the private competition data, authenticate owner-mirrored files, or inspect a submission-page receipt. The conclusions above do not claim those actions occurred.
