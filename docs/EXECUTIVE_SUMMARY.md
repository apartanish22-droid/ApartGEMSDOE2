# Executive summary — 28 October 2026

## Decision: no file is approved

**DO NOT SUBMIT.** This review generated no geological model or TIFF, selected no competition slot and did not replay a holdout. A previous session generated the H-TRACE research file, but its prior surface audit was incomplete and took place after dot placement; its final dots fail literal registry uniqueness. A different filename or hash is not a new geological method.

The usable visual decision desk is [index.html](index.html), and the current [submission guide](executive-summary.html) explains future gates. Nine [site briefs](index.html#scorecard) give archived filename, SHA-256, research-only download link, user-reported score and directional comparison. All nine historical dot sets exceed the 70% overlap threshold against another focus-site reference; those comparisons are not a complete current registry audit.

## Previous H-TRACE research file — negative

- **Identity:** `docs/downloads/apartgemsdoe2-trace-exp-2-trace-t1-22438dots-20261028T063240Z-71a21036-zeros.tif`, SHA-256 `32716d4851e9de2df406eeb2386c8ddcf9aa970c985643c7e5484973dd023b4f`.
- **Prior-session report, not independently replayed:** HOLDOUT-DTI 0.0893, 95% CI [0.0737, 0.1052], `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld-positive instances. No organizer-confirmed score or defensible hidden-leaderboard estimate exists for this file.
- **Uniqueness:** this review independently found 22,406/22,438 dots (99.86%) within 3 px of a pinned registry lattice. The prior surface receipt's maximum |Spearman| 0.1293 is incomplete and was checked too late to qualify as a pass. Do not exempt the lattice.
- **Saved-byte diagnostic:** one float32 band, EPSG:32611, 3730 × 3292, matching the owner mirror's transform; no nonfinite or out-of-range values inside its footprint. However, 7,111,787 exterior cells are unmasked finite values, and the reference mirror is not organizer-authenticated. The diagnostic fails; portal acceptance and the cause of the user's prior range rejection remain unknown. See [read-back](data/trace_readback_20261028.json) and [research page](trace/index.html).
- **Named mimics:** roads and rail embankments, Lake Lahontan shoreline benches, and airborne survey stripes. The previous canary results have not been independently reproduced for every feature.

[Current negative JSON run card](data/review_card_lattice_20261028.json) · [lattice geometry receipt](data/lattice_bounds_20261028.json) · [three-pass review](research/review-gates-20261028.md).

## What is known about 0.2778?

GEMSDOE32's **0.2778 is USER-REPORTED / UNVERIFIED**, not an authenticated file-bound score. Its 37,654 archived dots equal the 44,090-dot GEMSDOE25/30 support after removing 6,436 locations near the mirrored catalogue. Thinning or pruning may improve the official distance-weighted precision/coverage trade-off, but hidden truth and component scores are unavailable, so neither the cause nor a numerical forecast is established. The [official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) showed a higher value, 0.4544, on 28 October, but that observation does not validate a particular file here. [Full analysis](research/why-02778-and-how-to-beat-it-20261028.md).

## What must happen next?

Identify the explicitly assigned lane; restore authenticated competition inputs and the prepared shared stack; freeze and verify the complete registry; resolve open shared [registry #63](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/63) and [release-gate #67](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/67) issues upstream. Only then preregister a hypothesis, test every feature for leakage, compare a matched whole-segment buffered holdout, check surface uniqueness before placement and final-dot uniqueness against all entries, and validate saved bytes against the authenticated template. A separate selector must decide any slot. No alternative proposal is yet validated or approved.
