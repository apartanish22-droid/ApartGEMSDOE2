# ApartGEMS · evidence before the next upload

**Start every session here.** This repository is a research and decision desk for the [DOE GEMS Prize](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). The target is **geological faults**, not confirmed geothermal vents. Our objective is a genuinely new, high-quality, reproducible competition submission—not a copied TIFF, a renamed prior submission, an invented score, or a format-only pass.

> **CURRENT DECISION: DO NOT SUBMIT.** No new candidate TIFF, valid HOLDOUT-DTI, leaderboard estimate, or weekly-slot selection was produced. The run stopped at preflight. See the [executive guide](docs/executive-summary.html), [nine-site scorecard](docs/index.html#scorecard), [geometry audit](evidence/historical_audit.json), and [run card](evidence/run_card.json).

## Project brief: read this on every session

This section retains the substantive, non-duplicated instructions from the project prompt as the standing charter. Treat later explicit instructions and the competition's current rules as authoritative if they change.

- Review the highest supplied results from **GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36**. Provide an executive summary, source links, the exact file identity, estimate availability, uniqueness scope, and an obvious download/upload decision. The sites are independent repositories; this checkout publishes nine linked briefs, not edits to those repositories.
- Generate an original TIFF only when it can be responsibly validated; historical files may be downloaded **only for learning or comparison**. A changed filename, encoding, or hash alone does not make a new geological method. Never spend a slot on an unvalidated idea; negative results are deliverables.
- Before implementation propose **3–5 geological hypotheses**, naming the layers, physical signature, why it might detect unmapped faults, non-fault mimics, difference from prior work, qualitative rank and implementation cost. Verify free, official external data are actually obtainable and have appropriate reuse rights. Do not claim unproven global novelty. [The current slate](research/hypotheses.md) is untested and explicitly not an assigned lane.
- **PARALLEL-RUN PROTOCOL:**
  1. **Lane.** Stay inside the single assigned method paragraph. If surface rank correlation with any registry raster exceeds 0.90, or more than 70% of final dots lie within 3 pixels of any one registry raster, log a duplicate and stop. Check before placement **and** on final dots. Do not silently exempt calibration controls.
  2. **Reuse.** Use the shared template's cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`. Hide whole fault segments with a buffer; derive all catalogue features only from visible faults; mask visible faults pixel-exactly; score pooled distance-weighted Tversky with alpha 0.2, beta 0.8 and a 300 m triangular kernel. Fix any shared-tool defect in the shared template, not a private fork.
  3. **Label evidence.** New numerical performance results must be **HOLDOUT-DTI** with evaluator version, withheld-positive count and 95% CI, or **ORGANIZER-CONFIRMED** with a submission-page receipt. A projection is never a score. Historical user claims without receipts must remain explicitly **unverified**, not be relabeled as confirmed.
  4. **Leakage canary.** Test each feature individually; AUC above 0.90 is leakage until proven otherwise.
  5. **Run card.** Record hypothesis, mechanism, a named non-fault mimic, holdout and CI, registry correlation/overlap, raster SHA-256, saved-byte validation, submission name, a note of at most 140 characters, and verdict `promote` or `negative`. Use null for anything not measured.
  6. **Budget.** Stop after 3 experiments or 2 hours. A separate selector, respecting the current weekly cap on the authenticated submission page, determines any real slot. No human inspection is required for the project gates; a separate selector can be automated. Do not auto-submit.
- Design a clean GitHub Pages site with a prominent submission decision and, **only after all gates clear**, a simple download with a unique name and short note. Include an executive submission guide, verifiable official sources, honest freshness and data limitations. Automate checks; never call a stale snapshot a live feed.
- Investigate the user's reported portal rejection, `Predicted values must be in range [0, 1]`, using the exact saved bytes. Never claim its cause or portal acceptance without the rejected TIFF and a receipt. The official description says outside bounds are null/NaN, while some historical files use all-finite zeros; local diagnostics cannot adjudicate portal behavior.
- **Core values:** Maximize P(Win) by comparing risks and protecting scarce slots; Own the Outcome by documenting failures, fixing defects, verifying results, and making next steps explicit. Perform implementation, adversarial review, and final request reconciliation as separate passes.
- Follow [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), including data-use conditions and the generative-AI narrative disclosure where applicable. The rules PDF states three submissions per week; recheck the current authenticated page rather than assuming the allowance.

## Current findings (27 October 2026)

1. The initial checkout contained only this README; the claimed train→inference pipeline and cached stack were not present. No single geological method paragraph was supplied, so no lane was invented.
2. The [organizer's public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) displayed **0.4544** for its leader at the timestamp in [`docs/data/source_feed.json`](docs/data/source_feed.json). This is an **OFFICIAL PUBLIC LEADERBOARD OBSERVATION**, not a file-bound submission-page receipt. The prompt's 0.4413 and 0.3195 references are older/inconsistent snapshots.
3. The requested nine historical values, including GEMSDOE32's **0.2778**, are **USER-REPORTED / UNVERIFIED**: no organizer receipt binding a file hash to that value was available. No hidden-score estimate is defensible. Of the supplied claims, GEMSDOE32 is highest; that does not authorize resubmission.
4. We fetched immutable archival TIFFs **only for comparison**, hash-checked their bytes, and independently computed all 72 directional focus-site comparisons. All nine archived dot sets fail the literal overlap rule against at least one other focus-site reference. Pre-placement surfaces and a complete current registry are unavailable.
5. The registered 13GEMSDOE lattice covers 5,160,724 of 5,167,373 mirrored-footprint cells within 3 pixels. Only 6,649 are uncovered; at 37,654 distinct dots, at least `(37,654 − 6,649) / 37,654 = 82.34%` must overlap. This **GEOMETRY-AUDIT** stops a champion-sized run under the literal rule. It does **not** rule out every smaller budget. Never move dots into lattice holes merely to manufacture a pass.
6. The GEMSDOE32 archival support is a subset of the GEMSDOE31 support: 2,545 removed dots are within 2 pixels of the owner-mirrored catalogue. Reducing redundant/low-marginal-credit mass is plausible under the official DTI; hidden truth and a receipt are missing, so causation is not established and no improvement over 0.2778 can be promised.
7. The available owner-mirrored `sample_submission.tif` has 60,988 positive pixels identical to the mirrored labels, while the [organizer describes its sample](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format) as predicting total absence. Its bytes and geometry are hash-pinned but **not organizer-authenticated**. Use it only as a provisional forensic grid, not as official truth or final submission authorization.

## Files and reproduction

- `registry/historical-pins.json`: immutable archive, lattice, provisional template and label hashes; historical claims are unverified.
- `registry/shared-template-pins.json`: attribution and checksums for the existing [shared template](https://github.com/buffedlizard55-lab/GEMSDOE24/tree/2521cb676e172c141a4417e4925b73b6a896c1eb). No evaluator or writer is forked here.
- `scripts/restore_template.py`: restores those pinned source assets into ignored `.cache/` **without modification**. The selected assets alone are not a complete runnable template or prepared feature stack.
- `scripts/audit_historical.py`: reproduces the exact nine-file geometry and local format diagnostics. This is not a model, holdout evaluator, submission writer or portal validator. Prior TIFFs remain in ignored scratch storage.
- `scripts/preflight.py`: reports this run's blocked state and exits nonzero; it cannot authorize a submission. `evidence/preflight.json` is a timestamped snapshot, not a promise about future files.
- `scripts/build_site.py`: builds the static site and nine detail pages from committed evidence. `scripts/refresh_feed.py` updates timestamped public observations; scheduled GitHub Actions records failures as stale rather than fabricating freshness.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_template.py
.venv/bin/python scripts/audit_historical.py
.venv/bin/python scripts/preflight.py       # expected exit 1: BLOCKED
.venv/bin/python scripts/build_site.py
.venv/bin/pytest -q
python -m http.server 8000 --bind 0.0.0.0 --directory docs
```

`gh` and GitHub access are needed to restore the hash-pinned historical/source assets. Competition-sized data are not committed. The prepared 32-band feature cache, complete parallel registry, approved lane, authenticated template/receipts and current weekly allowance are not available here. The sandbox can reach GitHub and package registries directly; the competition data page redirects unauthenticated users to login, and direct USGS/DrivenData downloads are blocked by the sandbox network policy. Public official metadata was reviewed separately; source bytes and coverage were not verified unless the audit explicitly says so.

## Next work

Resolve the missing assigned lane and literal all-registry lattice rule **without unilaterally changing either**; recover the complete pinned template/cache and original authenticated sample; freeze a comparable leakage-safe best and complete registry; then run the top assigned hypothesis within the budget, canaries and both novelty checks. A separate automated selector may authorize a named, byte-validated TIFF only after all evidence clears. See [research/hypotheses.md](research/hypotheses.md) and [research/sources.md](research/sources.md).
