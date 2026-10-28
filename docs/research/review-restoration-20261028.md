# Review: restoration and nine-site replay — 28 October 2026

**Decision: no new TIFF is approved or generated.** No new experiment or slot was used. The prompt says a single method paragraph assigns the parallel lane, but no such paragraph is identifiable. Inventing one would conflict with the lane protocol. A separate selector must approve any future promotion; a format pass alone is not approval. [Current run card](../../evidence/current_review_run_card.json).

## Pass 1: recover and verify

Using the pinned GitHub mirrors, `scripts/restore_data.py` restored the feature raster, label raster, existing-fault raster, sample mirror, external SGMC mirror, nine historical comparison variants and lattice to ignored scratch storage. After the fix below, all four core-file hashes matched the owner pins in `registry/data_manifest.json`. The two label/fault files have the same hash; this is a property of the mirrors, not independent authentication. The pinned sample is identical to the labels within its footprint, an anomaly already recorded in the [historical audit](../../evidence/historical_audit.json). **Hash agreement is not proof that these files came from the organizer.** The prepared shared feature stack and complete parallel registry are still unavailable. The nine pinned shared template assets were restored and hash-checked; they are not a complete runnable template.

The read-only `scripts/verify_independent_replays.py` reproduced every recorded field (apart from observation time) of both the historical nine-site and AP-1 geometry audits. This is a geometry replay, not a holdout replay or validation of the user-reported scores. The [nine-site table](../index.html#scorecard) identifies each claimed historical best, estimated new-file score as unknown, and observed pairwise duplicate status. Its archival variants may differ from the exact scored bytes.

The [GEMSDOE32 page source](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/index.html) itself describes its 0.2778 as an **owner report** without a hash-bound submission receipt. The independent raster replay supports a possible explanation: the archived B2 mask removes near-catalogue dots from a related historical support, which may reduce wasted prediction mass in a distance-weighted score. Neither the hidden truth nor a controlled organizer ablation is available, so this does not establish causation or whether a new approach can exceed that value. No numerical leaderboard estimate is justified.

## Pass 2: fixes

* The restoration script omitted `existing_faults.tif` even though preflight treats it as core. It now restores that pinned file, rejects missing or duplicate required manifest IDs before download, and tells users how to point preflight to the chosen directory. The original historical receipt is not proof of current files.
* The static home page no longer displays an old leaderboard value when JavaScript is disabled or fails before loading its feed. The H-TRACE result is now correctly attributed to an earlier run, not this review. The scheduled feed remains a timestamped snapshot, not a guaranteed current leaderboard.
* Regression tests cover the restore manifest and the generated homepage. The first test pass detected that the generated HTML had not yet been rebuilt; the page was rebuilt before the final test pass.

## Pass 3: remaining gates and access

* An explicit lane and complete frozen registry are needed before any new experiment. The literal overlap rule includes the pinned calibration lattice; the replay confirms its champion-sized minimum overlap exceeds the requested threshold. Do not exclude it silently or manufacture dots in its holes.
* Obtain the authenticated [competition data and sample](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) under the competition rules; confirm footprint, exterior/nodata behavior and weekly allowance with the organizer. The sandbox cannot reach DrivenData, Dropbox, USGS or GDR directly because of its outbound allowlist. Existing mirrors are accessible but their origin is not independently verified.
* Restore or reproduce the shared prepared feature stack, then use the shared evaluator/writer and verify every individual feature's leakage canary. Run whole-segment, buffered hide-and-recover folds with catalogue-derived features built from visible faults only; assess both pre-placement surfaces and emitted dots against the complete registry. Compare with a matched, independently replayed control and report the evaluator, withheld-positive count and spatial confidence interval. Do not equate holdout DTI with hidden leaderboard performance.
* The earlier [five ranked proposals](../../knowledge/preregistration_trace_20261028.md) are historical, not newly validated or assigned. In particular, the first was already tested and rejected; the InSAR idea's external data was not verified obtainable here. Do not present them as new work completed in this review. The condensed [standing prompt](standing-prompt-ap2.md) is not a verbatim copy of the current lengthy request.
* The official [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) documents CPU-only as well as GPU setups; a GPU is not an established universal prerequisite. The official [problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) could not be independently rechecked from this sandbox.

Reproduce the restored-mirror checks locally (the restored inputs are ignored and must be fetched again in a fresh checkout):

```sh
python -m pip install -r requirements.txt
python scripts/restore_template.py
python scripts/restore_data.py --target-dir .cache/review-data
GEMS_DATA_DIR="$PWD/.cache/review-data" python scripts/preflight.py  # remains BLOCKED
python scripts/verify_independent_replays.py
python scripts/build_site.py && python scripts/build_scorecard.py
python -m pytest -q
node tests/feed_ui.cjs && node --test tests/js/source_freshness.test.cjs
```

This is a negative research deliverable, not permission to submit a prior or new raster.
