# ApartGEMS · evidence before the next upload

**Start every session here.** This repository is a research and decision desk for the [DOE GEMS Prize](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). The target is geological faults, not confirmed geothermal vents. We seek a genuinely new, high-quality, reproducible competition submission—not a copied TIFF, renamed prior submission, invented score, or format-only pass.

**Arena AI Core Values:** **Maximize P(Win)** · **Own the Outcome**

> ## CURRENT DECISION: DO NOT SUBMIT
> **No candidate is approved; no new experiment or weekly slot was used in the latest review.** The H-TRACE and H-UDSR files below are historical research artifacts, not submission downloads. Their literal lattice overlaps exceed 70%; their owner-mirrored template is not organizer-authenticated. A newly verified flaw in the archived holdout split also means the prior numbers do **not** establish the requested buffered-whole-segment validation. The archived surface check was incomplete and, for H-TRACE, happened after dot placement.
>
> [Current JSON run card](evidence/current_run_card.json) · [Executive summary and guide](docs/executive-summary.html) · [Nine-site scorecard](docs/index.html#scorecard) · [Three-pass review](docs/REVIEW_20261028_FOLLOWUP.md)

## Standing project prompt — read on every session

This is the durable, consolidated operational request; [PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) preserves the longer brief and source links. Later explicit user instructions and current official rules take precedence.

- Review the highest supplied results from **GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36**. Provide an executive summary, source links, exact file identities, evidence-labeled results or estimates, uniqueness scope, and an obvious download/upload decision. Investigate the reported GEMSDOE32 **0.2778** result without equating a user claim or a projection with an organizer receipt. Check the current official leaderboard rather than accepting older conflicting top-score claims.
- Generate an **original** competition-format GeoTIFF only when it can be responsibly validated; prior files may be used for learning or comparison, not copied as a new prediction. A changed filename, encoding, or hash alone is not a new geological method. Negative results are deliverables; do not spend a slot on an unvalidated idea.
- Before implementation, rank **3–5 geological hypotheses** with their exact layers, physical signature, reason they may detect unknown faults, distinction from past work, named non-fault mimics, expected improvement or uncertainty, implementation cost, and data/rights viability. Verify official free external data are actually obtainable and cover the area before calling an idea viable. Do not claim unproven global novelty.
- **Parallel-run protocol:**
  1. **Lane:** stay inside the single explicitly assigned method. Check the candidate surface against **every** registry raster before dot placement, then final dots; stop and log duplicate if rank correlation exceeds 0.90 or more than 70% of dots are within 3 pixels of any reference. Never silently exempt the calibration lattice.
  2. **Reuse:** use the shared template's cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`. Hide whole fault segments with a buffer; derive all catalogue features only from visible faults; mask visible faults pixel-exactly; score pooled distance-weighted Tversky with α=0.2, β=0.8 and a 300 m triangular kernel. Fix defects once in the canonical shared template, not a private fork. The pinned shared tools in this checkout have unresolved upstream defects and must not be used for a fresh experiment until corrected and re-pinned.
  3. **Evidence:** label every new numeric performance result **HOLDOUT-DTI** with evaluator version, withheld-positive count and 95% CI, or **ORGANIZER-CONFIRMED** with an organizer submission-page receipt. Estimates/projections are not scores. Historical values without receipts remain explicitly **user-reported / unverified**.
  4. **Leakage:** test each feature individually; AUC above 0.90 is leakage until disproved. A lower AUC is not proof that leakage is absent.
  5. **Run card:** record hypothesis, mechanism, named non-fault mimic, holdout and CI, registry correlation/overlap, raster SHA-256, saved-byte validation including footprint NaNs and [0,1], CRS/shape/transform, unique name, note ≤140 characters, and verdict `promote` or `negative`. Use null for unmeasured quantities.
  6. **Budget:** stop after three experiments or two hours. Before any slot, the top candidate must beat a frozen same-protocol holdout best with uncertainty-aware, matched comparison. A **separate selector**, respecting the authenticated weekly cap, decides whether a real slot is justified. Do not auto-submit.
- Publish a clean GitHub Pages site with an obvious decision and **only after all gates clear** a submission download, name, short note and guide. Include exact file/evidence tables, trustworthy official sources, timestamped freshness and scientific/format/access limitations. Automate checks; do not call a stale snapshot live. Investigate the user's reported `[0,1]` portal error only from the actual rejected bytes; do not guess at its cause.
- Follow the [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), including data-use conditions and generative-AI disclosure. Work autonomously where feasible, conduct three sequential implementation/review/fix passes, document remaining blockers and create a PR; merge it only if the repository allows it and checks pass.

## What the latest review established

1. **No valid new candidate:** the parallel AP-1 and earlier H-TRACE lanes each reported three experiments; the prompt does not identify a new explicit lane. No new model, prediction, TIFF, organizer submission or leaderboard estimate was generated in this review. The four unrun qualitative proposals are in [the research slate](knowledge/preregistration_review_20261028.md).
2. **Holdout split is not the promised protocol:** on hash-verified owner mirrors, the archived `GEMSDOE32-HIDE-RECOVER-v3.0` split puts **15,705 / 22,232** withheld-positive occurrences within 15 pixels of visible catalogue faults; nearest separation is 2 pixels in each cell and **76** component instances are partially scored. The eight cells include repeated draws; these are geometry counts, not scores. See the [independent receipt](evidence/shared_split_geometry_20261028.json) and [canonical issue #60](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/60). A prior HOLDOUT-DTI value is retained as an archived diagnostic, not as validated evidence under the requested protocol.
3. **Registry/placement:** H-TRACE's surface audit was performed after dot placement and had two malformed/missing entries, so its reported 0.1293 maximum correlation is not an all-registry pre-placement pass. Its saved TIFF has **22,406 / 22,438 = 99.857%** dots within 3 pixels of the registered lattice ([saved-byte audit](evidence/trace_independent_recheck_20261028.json)), above 70%. No density exemption is allowed. The shared auditor's fail-open paths are reported at [issue #63](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/63).
4. **Format is not approval:** the archived H-TRACE TIFF has SHA-256 `32716d4851e9de2df406eeb2386c8ddcf9aa970c985643c7e5484973dd023b4f`; its finite [0,1] cells and grid match an owner mirror, but its unmasked exterior zeros do not satisfy the conservative null/NaN-outside reading. The organizer template, portal acceptance and cause of the user's earlier rejection are unverified. The older H-UDSR artifact has SHA-256 `1f2c28e9eba172fe6a4da138b98afa28a43420549e174c801a02af658ef180b9` and also fails the lattice rule. The H2 fractal file is a seeded synthetic demo, not a competition-data prediction.
5. **History and scores:** the [historical audit](evidence/historical_audit.json) was independently replayed from pinned bytes; all nine archived dot sets fail the 70% overlap rule against another focus-site raster. B2 is a two-pixel catalogue-collar-pruned subset of D2.8; this may reduce redundant false-positive mass but does not establish why an unverified **0.2778** was reported or predict hidden-test performance. The organizer's public leaderboard showed **0.4544** on 28 October 2026 UTC, an observation—not a file-bound receipt and not necessarily current. New-file leaderboard estimate: **unavailable**.
6. **Shared tools:** keep the ten files in `data/shared_tool_hashes.txt` byte-identical to their pins. Additional open reports include the [zero-truth false-positive bug #41](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41), [static-input labeling #61](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/61), and probability-binarizing [writer/evaluator #37](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/37) / [#51](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/51). This account has read-only access to the canonical repositories; these are blockers, not locally fixed shared code. The shared writer and evaluator are still directly callable and unsafe for a new run; **do not call them until the upstream fixes land**.

## Reproduce the read-only checks

A fresh checkout does not include ignored caches. Hashes verify owner mirrors, **not** organizer origin. Restoring the core includes a ~419 MB feature raster; do not confuse historical restore receipts with current files.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py --target-dir .cache/gems_data
.venv/bin/python scripts/restore_template.py
.venv/bin/python scripts/fetch_audit_data.py
.venv/bin/python scripts/restore_shared_tools.py
.venv/bin/python scripts/verify_independent_replays.py
GEMS_DATA_DIR=.cache/gems_data .venv/bin/python scripts/audit_shared_splits.py  # geometry only
.venv/bin/python scripts/recheck_trace.py                                     # bytes + lattice only
GEMS_DATA_DIR=.cache/gems_data .venv/bin/python scripts/preflight.py          # exits 1: BLOCKED
sha256sum --check data/shared_tool_hashes.txt
.venv/bin/pytest -q
node tests/feed_ui.cjs
node --test tests/js/source_freshness.test.cjs
.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_scorecard.py
```

The old H-TRACE/AP-1/AP2/H-UDSR runners and local exporters are guarded; the old H2 generator stops unconditionally. They are not reproduction instructions for a new experiment. The shared pinned CLIs remain unchanged and are explicitly **not** safe substitutes. A green local format check does not establish an authenticated template, official format compliance or slot authorization.

## Next steps

Authenticate original competition inputs and sample; obtain a real lane assignment and fresh budget; have canonical maintainers correct and pin shared split/metric/writer/registry defects; verify the shared feature stack and complete registry; resolve the literal lattice issue without changing the rule; then re-run per-feature canaries, a surface check before any placement, a buffered matched holdout and final-dot audit. A separate selector may evaluate the weekly allowance only after all gates pass. If these conditions remain unmet, keep the negative result and do not submit.

Primary sources: [competition problem and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), [rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program), and [DOE INGENIOUS](https://gdr.openei.org/submissions/1391).
