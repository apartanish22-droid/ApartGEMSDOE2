# Independent review and reconciliation — 28 October 2026

**Decision:** `negative`. This review ran zero geological experiments, created
no new prediction TIFF, and used zero weekly slots. The requested unique,
higher-scoring submission remains unfulfilled. The current
[machine-readable run card](../../evidence/current_run_card.json) contains nulls
rather than invented candidate measurements.

## Pass 1 — implementation and evidence

- Re-read the standing [project brief](../PROJECT_BRIEF.md) and nine-site
  historical claims. Re-fetched the pinned public comparators, a partial
  read-only shared-tool set, and core owner mirrors; verified their SHA-256
  values. Mirror consistency is not organizer authentication.
- Replayed the nine-site and AP-1 raster audits. The archived GEMSDOE32 result
  remains a user-reported 0.2778, not a file-bound organizer receipt. The
  measured geometry is consistent with pruning redundant dots, but does not
  establish the cause of a reported score.
- Read back the pre-existing H2 demo against the mirrored footprint and a pinned
  lattice. It is synthetic; `nodata=0` masks 5,140,874 inside cells, and
  26,478/26,499 in-footprint dots are within three pixels of the lattice.
  [Deterministic receipt](../../evidence/h2_saved_byte_recheck_20261028.json).

## Pass 2 — bugs and edge cases

- DrivenData's [published terms](https://www.drivendata.org/termsofuse/)
  prohibit automatic website access for monitoring. Removed scheduled
  leaderboard fetching; the Pages feed checks GitHub source heads only. Added
  direct-host and redirect safeguards plus stale/disabled UI tests.
- Retired old experiment and emission entry points: a future READY preflight
  alone cannot fix their missing pre-placement stop, final literal check and
  two-hour enforcement. The H2 CLI no longer writes another pseudo-feature demo.
- Added a separate local evidence selector and CLI. It fails closed on missing
  authority, incomplete or unbound registry checks, absent feature canaries,
  unmatched fold/evaluator hashes, missing saved-byte checks and a nonpositive
  paired interval. It never approves or spends a slot. The CLI ignores any
  preflight assertion embedded in an input receipt and consults the current
  automated preflight. This is **not** a shared-tool patch.
- Upstream pinned-tool issues remain open: GEMSDOE32 [#37](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/37),
  [#41](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41),
  [#61](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/61),
  [#63](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/63),
  [#67](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/67), and
  GEMSDOE24 [#74](https://github.com/buffedlizard55-lab/GEMSDOE24/issues/74)/
  [#77](https://github.com/buffedlizard55-lab/GEMSDOE24/issues/77). This account
  has no push permission there. The pinned shared files remain byte-identical;
  no private shared-tool fix was made.

## Pass 3 — reconciliation with the request

- Replaced contradictory H2 upload/uniqueness claims and unsupported score
  projections in the summary, status text and card. Corrected the B2 causal
  analysis and made the Pages upload decision and current card prominent.
- Kept four qualitatively ranked research proposals with mechanisms, layers,
  non-fault mimics, implementation cost and official source listings. Exact
  product bytes, licenses where noted, target coverage and uniqueness remain
  unverified in this environment. A publication listing is not a successful
  download or model evaluation.
- Preflight remains blocked: no explicit assigned lane, complete parallel
  registry, verified shared feature cache, authenticated organizer template,
  independent comparable best or `existing_faults.tif`. The lattice counting
  bound is conditional on the example dot count and is not evidence against all
  smaller sets. Do not infer the cause of the separate portal range error: the
  rejected bytes are unavailable.

The historical research TIFFs remain labeled **RESEARCH ONLY / DO NOT SUBMIT**.
A separate selector is required even if a future candidate passes every gate.
