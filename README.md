# ApartGEMS · evidence before the next upload

**Start every session here.** This repository is an evidence and decision desk for the [DOE GEMS Prize](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). The task is geological-fault prediction, not proof of a geothermal vent or reservoir. **Arena AI Core Values: Maximize P(Win) · Own the Outcome.**

> **CURRENT DECISION: DO NOT SUBMIT.** No new TIFF is authorized. This review used no geological experiment or weekly slot. The prior H-TRACE, H-UDSR, AP1 and AP2 files are research-only and fail literal registry uniqueness; the H2 file is a synthetic demo. Historical values are unverified, and a different hash is not a novel method.

The [decision desk](docs/index.html), [submission guide](docs/executive-summary.html), [H-TRACE research record](docs/trace/index.html), and [current negative run card](evidence/review_card_lattice_20261028.json) give the evidence and limitations. Original older narrative remains in Git history.

## Project brief: read this on every session

This section retains the substantive, non-duplicated instructions from the project prompt as the standing charter. Treat later explicit instructions and the competition's current rules as authoritative if they change.

- Review the highest supplied results from **GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36**. Provide an executive summary, source links, the exact file identity, estimate availability, uniqueness scope, and an obvious download/upload decision. The sites are independent repositories; this checkout publishes nine linked briefs, not edits to those repositories.
- Generate an original TIFF only when it can be responsibly validated; historical files may be downloaded **only for learning or comparison**. A changed filename, encoding, or hash alone does not make a new geological method. Never spend a slot on an unvalidated idea; negative results are deliverables.
- Before implementation propose **3–5 geological hypotheses**, naming the layers, physical signature, why it might detect unmapped faults, non-fault mimics, difference from prior work, qualitative rank and implementation cost. Verify free, official external data are actually obtainable and have appropriate reuse rights. Do not claim unproven global novelty.
- **PARALLEL-RUN PROTOCOL:**
  1. **Lane.** Stay inside the single assigned method paragraph. If surface rank correlation with any registry raster exceeds 0.90, or more than 70% of final dots lie within 3 pixels of any one registry raster, log a duplicate and stop. Check before placement **and** on final dots. Do not silently exempt calibration controls.
  2. **Reuse.** Use the shared template's cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`. Hide whole fault segments with a buffer; derive all catalogue features only from visible faults; mask visible faults pixel-exactly; score pooled distance-weighted Tversky with alpha 0.2, beta 0.8 and a 300 m triangular kernel. Fix any shared-tool defect in the shared template, not a private fork.
  3. **Label evidence.** New numerical performance results must be **HOLDOUT-DTI** with evaluator version, withheld-positive count and 95% CI, or **ORGANIZER-CONFIRMED** with a submission-page receipt. A projection is never a score. Historical user claims without receipts must remain explicitly **unverified**, not be relabeled as confirmed.
  4. **Leakage canary.** Test each feature individually; AUC above 0.90 is leakage until proven otherwise.
  5. **Run card.** Record hypothesis, mechanism, a named non-fault mimic, holdout and CI, registry correlation/overlap, raster SHA-256, saved-byte validation, submission name, a note of at most 140 characters, and verdict `promote` or `negative`. Use null for anything not measured.
  6. **Budget.** Stop after 3 experiments or 2 hours. A separate selector, respecting the current weekly cap on the authenticated submission page, determines any real slot. No human inspection is required for the project gates; a separate selector can be automated. Do not auto-submit.
- Design a clean GitHub Pages site with a prominent submission decision and, **only after all gates clear**, a simple submission download with a unique name and short note. Include an executive submission guide, verifiable official sources, honest freshness and data limitations. Automate checks; never call a stale snapshot a live feed.
- Investigate the user's reported portal rejection, `Predicted values must be in range [0, 1]`, using the exact saved bytes.
- **Core values:** **Maximize P(Win)** by comparing risks and protecting scarce slots; **Own the Outcome** by documenting failures, fixing defects, verifying results, and making next steps explicit. Perform implementation, adversarial review, and final request reconciliation as separate passes.
- Follow [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), including data-use conditions and the generative-AI narrative disclosure where applicable.

## Current review · 28 October 2026

- **Historical reports, not receipts.** Highest supplied values for GEMSDOE24/25/27/28/30/31/32/33/36 are 0.2477 / 0.2600 / 0.2449 / 0.2710 / 0.2600 / 0.2708 / 0.2778 / 0.2632 / 0.2750. Every value is **USER-REPORTED / UNVERIFIED**; a receipt binding a file hash to a score was not available. [Nine-site briefs](docs/index.html#scorecard) give archival identities, links and directional comparisons. Repository HEADs have moved since the pinned archives; monitoring HEADs is not auditing newer files.
- **Why 0.2778 might lead.** The pinned GEMSDOE32 B2 dots equal the 44,090-dot GEMSDOE25/30 support after removing 6,436 dots within two pixels of the mirrored catalogue. The 25 and 30 dot positions match but their file bytes do not. Thinning and pruning could improve the published distance-weighted precision/coverage trade-off, but no receipt or hidden labels establish the cause or a forecast. [Analysis and official sources](docs/research/why-02778-and-how-to-beat-it-20261028.md).
- **Literal lattice conflict.** The pinned spacing-5 lattice leaves just 6,649 of 5,167,373 mirror-footprint cells beyond three pixels. Above 22,163 distinct dots, passing the 70% overlap rule is impossible. With minimum spacing ≥2.8 px, the necessary maximum is 9,930; with ≥2.9 px, it is 8,260. These are upper bounds, not sufficient conditions, geological results, or permission to exploit edge holes. [Reproducible audit](evidence/lattice_bounds_20261028.json).
- **Prior H-TRACE result.** A previous session reported HOLDOUT-DTI 0.0893, CI [0.0737, 0.1052], `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld-positive instances. This review did not replay it. The archived surface audit was incomplete and ran after placement. Independently, 22,406/22,438 saved dots (99.86%) fall within 3 px of the lattice. [Research record](docs/trace/index.html); verdict **negative**.
- **Prior H-UDSR artifact identity.** SHA-256 `1f2c28e9eba172fe6a4da138b98afa28a43420549e174c801a02af658ef180b9`; 26,135/26,173 saved dots fall within three pixels of the lattice. Research only; no upload.
- **Exact-byte format check.** [Read-back evidence](evidence/trace_readback_20261028.json) verifies finite [0,1] in the mirror footprint, float32, EPSG:32611 and matching grid, but finds 7,111,787 unmasked finite exterior cells. The mirror's supposedly blank template also contains 60,988 label-identical positives. The template is not organizer-authenticated, the local format check fails, and neither portal acceptance nor the cause of the reported range error is known.
- **H2 is not implemented as claimed.** The saved H2 raster uses pseudo-features; its real-data map builder combines multiscale gradients instead of invoking its advertised fractal/azimuth helpers. Its entry point is blocked. [Correction](docs/EXECUTIVE_SUMMARY_H2.md).
- **Shared fixes are not private forks.** Shared sources were kept byte-identical to their upstream pins. Defects and missing proofs are open upstream: [GEMSDOE24 template #74](https://github.com/buffedlizard55-lab/GEMSDOE24/issues/74), [GEMSDOE32 registry #63](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/63), and [release gate #67](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/67). This account cannot push to the shared repository; no upstream fix is claimed. Historic H-TRACE/H-UDSR runners and emitters remain permanently blocked even if preflight changes.
- **Research slate.** Four ranked proposal-only ideas, named mimics, and official source/reuse caveats are in [research/hypotheses.md](research/hypotheses.md). Published source descriptions do not prove local data coverage or that bytes can be retrieved here. None was tested in this review.

## Reproduce the read-only checks

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/fetch_audit_data.py     # hash-pinned public comparators, not organizer authentication
.venv/bin/python scripts/restore_template.py       # read-only pinned source; not the missing feature stack
.venv/bin/python scripts/preflight.py              # expected BLOCKED
.venv/bin/python scripts/audit_lattice_feasibility.py --candidate data/audit/GEMSDOE32.tif
.venv/bin/pytest -q
node tests/feed_ui.cjs
node --test tests/js/source_freshness.test.cjs
.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_scorecard.py
```

`audit_lattice_feasibility.py` is forensic and never creates a candidate. Archived generators are deliberately not a quick-start route. The current session's exact five-file lattice receipt and read-back report can be rerun from their scripts and pinned inputs; no human visual inspection is required.

## Blockers and next action

The prompt refers to a single method paragraph but does not identify one; no new lane is inferred. The prepared shared feature stack, complete current registry, authenticated competition sample, and authenticated weekly allowance are unavailable. Request or establish these inputs and the assigned lane; wait for reviewed shared-tool fixes; then, only under an authorized experiment budget, preregister and test the assigned hypothesis with whole-segment buffered holdout, every-feature canaries, pre-placement and final literal uniqueness checks, saved-byte validation, and a separate selector. No weekly upload follows automatically.

Official starting points: [problem and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), [rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program), and [DOE GDR 1391](https://gdr.openei.org/submissions/1391). A public data landing page is not verification of target-area binary access or a submission receipt.
