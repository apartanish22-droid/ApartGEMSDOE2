# Repository review — 30 October 2026

## Decision

**NEGATIVE — no GeoTIFF is approved to download and submit.** This review generated no scientific experiment, prediction surface, TIFF, score estimate, organizer upload, or weekly-slot selection. The current fail-closed preflight says `BLOCKED`; the requested holdout cannot be run from the present checkout. Do not treat a historical `-zeros.tif` as a submission-ready alternative.

This is a repository-state review, not a fresh confirmation of external webpages. Competition figures supplied in the user prompt are **USER-REPORTED / UNVERIFIED** in this review. No new number below is presented as `HOLDOUT-DTI` or `ORGANIZER-CONFIRMED`.

## Focus-site executive comparison

The table below transcribes the highest score provided for each requested site in the prompt. File identities are the reported artifact names; available archived bytes and peer-overlap analysis are described in the repository's [nine-site executive summary](EXECUTIVE_SUMMARY.md) and [forensics pages](forensics/). Scores are not bound to organizer receipts and cannot be treated as comparable estimates of a new submission's hidden score.

| Site | Prompt-reported best artifact | Prompt-reported score | New-file estimate | Uniqueness / decision |
|---|---|---:|---|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | Not estimable | Archived peer analysis says duplicate-like; do not submit |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | Not estimable | Archived peer analysis says duplicate-like; do not submit |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | Not estimable | Archived peer analysis says duplicate-like; do not submit |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | Not estimable | Archived peer analysis says duplicate-like; do not submit |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | Not estimable | Archived analysis identifies duplicate support with GEMSDOE25; do not submit |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | Not estimable | Archived peer analysis says duplicate-like; do not submit |
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | Not estimable | User-reported result; archived peer analysis says duplicate-like; do not submit |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | Not estimable | Archived peer analysis says duplicate-like; do not submit |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | Not estimable | Archived peer analysis says duplicate-like; do not submit |

**Score caveat:** each numeric score in this table is exactly the user's supplied historical value, not a value recalculated by this review. “Not estimable” is intentional: there is no validated, matched buffered holdout or calibrated mapping to the hidden leaderboard for a new candidate. Candidate dot count, method novelty, or prior-site score does not produce a defensible score estimate.

## What may explain the reported GEMSDOE32 0.2778

The repo's saved-byte analysis says the archived B2 dot support is the D2.8 support after removing cells within two pixels of the owner-mirrored catalogue, and it is also a subset of the archived GEMSDOE31 support. In the DTI, a prediction that earns no additional nearby truth credit can still add false-positive mass, so removing redundant predictions is a plausible way to improve DTI. The same pruning can hurt if it removes predictions that best match hidden faults. Without hidden truth and a receipt linking the submitted file bytes to 0.2778, the mechanism is a **hypothesis**, not a causal explanation. The exact derivation and limitations are documented in [Why 0.2778?](research/why-02778-and-how-to-beat-it-20261028.md).

The user's stated current leaderboard high of **0.3195** is USER-REPORTED / UNVERIFIED here. The repository feed's **0.4544** is an older public-leaderboard observation last attempted on 27 October 2026, not current evidence and not a receipt for B2. `docs/data/source_feed.json` and `docs/data/source_heads.json` are stale relative to this review date; their timestamps must be shown as stale, not represented as a live feed.

## Review passes

### Pass 1 — inventory and evidence

- Read the README standing prompt, executive summary, current run card, focus-site forensic documents, preregistered hypothesis slate, historical comparison, and validation/preflight code.
- Confirmed this checkout is on `arena/600928cb-apartgemsdoe2`, with no pre-existing working-tree changes at review start.
- The existing four untried candidates are documented in [hypotheses_untried.md](research/hypotheses_untried.md), with layers, physical signature, missing-catalogue rationale, mimics, differentiation, data provenance/availability status, and qualitative cost/rank. They are proposals, not validated viable methods. The protocol also has no explicit user-assigned lane, so no candidate was selected or run.

### Pass 2 — executable checks and adversarial review

- Installed the pinned Python dependencies in an ignored `.venv` and ran the complete test suite: **183 passed, 9 skipped, 4 unittest subtests passed**. Rasterio emitted 65 `PendingDeprecationWarning`s. The skipped tests depend on absent competition data or candidate fixtures; passing unit tests do not validate scientific performance or external inputs.
- `node tests/feed_ui.cjs` passed the success/stale/failure UI checks. `node --test tests/js/source_freshness.test.cjs` passed 2 tests.
- `git diff --check` passed. The two independently cited research TIFFs were hash-checked against their archived receipts: TRACE `32716d...23b4f` and SAR-PU `030153...5aa82`. They remain research-only, not approved downloads.
- Ran `scripts/preflight.py`: **BLOCKED**. Current competition rasters, sample, cached feature stack, and pinned shared-template assets are absent. It reports no assigned lane, an incomplete registry, unresolved shared-tool defects, and no submission authorization.
- Tried `scripts/verify_independent_replays.py`; it stopped because `data/audit/lattice.tif` is missing. This is an input-availability failure, not an audit pass or evidence that the saved receipts are wrong.
- Rebuilt the static site and scorecard; the generators completed without producing working-tree changes. Current published-feed data remain stale as noted above.

### Pass 3 — requirement reconciliation

- **Unique TIFF:** not generated. The checked-out artifacts have historical failures of the literal registered-lattice rule; no candidate satisfies the required all-registry pre-placement and final-dot gates.
- **Score:** no holdout score or projection was made. The only accurate estimate for a new candidate is unavailable.
- **Format:** no new file was made to validate. Existing mirror-grid checks are not validation against the authenticated competition sample, and no claim is made about portal acceptance or the user's earlier `[0,1]` rejection.
- **Experiments/budget:** zero experiments and zero weekly slots used in this review. Archived parallel work already reports three experiments in its lane; do not treat this as a reset or permission to exceed its budget.
- **Publication/release:** historical score rows are clearly qualified; do not surface any old TIFF as an OK-to-submit file.

## Ranked next hypotheses and blockers

Use the already documented [candidate slate](research/hypotheses_untried.md); do not start another private fork. Its qualitative rankings are not DTI estimates. The top listed proposal is H–C1 (BLM closed mineral-claim proximity × GeoDAWN radiometrics), followed by H–C2 (shallow-temperature anomalies × radiometrics), H–C3 (NASA OPERA InSAR), and H–C4 (deep-crust conductance ratio). The slate itself marks critical coverage, provenance, rights, or retrieval as **unverified**; therefore none is currently viable to run. H–RAD is recorded as an already-run negative, not a new candidate.

Before any new experiment: authenticate the original organizer data/template; restore and verify the cached shared feature stack; resolve upstream holdout/evaluator/writer/registry issues once in the canonical template; establish the requested buffered whole-segment holdout; verify a complete registry and lattice rule; agree the single lane and remaining budget; then run feature-wise leakage canaries and a matched, uncertainty-aware holdout comparison. Only a distinct selector may assess a weekly slot after every gate passes.

## Run card (JSON)

See [machine-readable run card](../evidence/repo_review_run_card_20261030.json). Verdict: **negative**. No candidate TIFF, score, or submission name/note exists for this review.
