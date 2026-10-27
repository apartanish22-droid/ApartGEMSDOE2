# ApartGEMSDOE2 — evidence-led GEMS fault discovery

> **Start here every session.** Read this README, [the standing project brief](docs/PROJECT_BRIEF.md), and [the executive review](docs/EXECUTIVE_REVIEW.md) before doing research, training, or packaging. **Current decision: NO TIFF is approved to submit.** A parallel-session file is available for research only.

## Mission and standing brief

Build a scientifically defensible, auditable workflow for the [DOE GEMS Prize](https://www.drivendata.org/competitions/306/competition-doe-gems/): predict previously unmapped geological faults relevant to geothermal exploration, and publish an easy-to-find, unique submission **only after** it passes all scientific, registry, file-format and slot-selection gates. A predicted fault is not a verified geothermal vent. Maximize the probability of a robust result, not merely a public leaderboard snapshot.

The user's operative instructions, preserved as the starting point for every session:

> **Maximize P(Win).** Weigh tradeoffs, assess risk, and choose the path that maximizes the probability of success.
>
> **Own the Outcome.** Own results end to end. Treat failure and success as signals and use them to improve.
>
> **MUST GENERATE A UNIQUE TIF SUBMISSION. DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.** It must be obvious whether it is OK to download and submit the generated TIFF. Validate through the project without manual inspection; supply a unique name and a short note when a candidate is actually approved.
>
> **PARALLEL-RUN PROTOCOL.** Follow the single assigned method lane. Stop if rank correlation with any registry raster exceeds 0.90 or more than 70% of candidate dots fall within 3 pixels of a registry raster, checking the pre-placement surface and final dots. Reuse the template cache, `evaluate_holdout.py` and `submission_writer.py`; never maintain a private fork. Hide whole fault segments with a buffer, rebuild all catalogue features from visible faults only, mask visible faults pixel-exactly, and pool distance-weighted Tversky with alpha 0.2, beta 0.8, and a 300 m triangular kernel. Test each feature alone; AUC above 0.90 is leakage until resolved. Label HOLDOUT-DTI with evaluator version, withheld positives and 95% CI; call a score ORGANIZER-CONFIRMED only with a submission-page receipt. Projections are not scores. Stop after three experiments or two hours. Promotion to a weekly slot is a separate selector step.
>
> Before implementing a method, rank 3–5 candidate geological hypotheses by expected improvement and cost, name their layers, physics, non-fault mimics and differences from prior work, and verify any required external data source. Validate the top candidate on the buffered spatial holdout and against the current same-evaluator best before considering a weekly slot. Record one JSON run card with hypothesis, mechanism, mimic, holdout DTI and CI, registry comparison, raster SHA-256, validator output, submission name and ≤140-character note, and promote/negative verdict. Negative results are deliverables.

The full durable operational brief, including the nine priority sites and the user's sources and release goals (with repeated text consolidated), is in [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md).

## Current state

- **No approved candidate, no leaderboard estimate, no approved slot.** A parallel session created [AP-1](docs/downloads/apartgemsdoe2-ap1-dilatcond-37654-20261027-1f26aa05-zeros.tif) for research only. Its 37,654 saved dots overlap the lattice by **99.72%**, so it fails the user's literal novelty rule. The prompt does not identify the assigned lane; a parallel preregistration selected AP-1 but does not establish external assignment. The full current registry and organizer-authenticated sample are missing; this audit did not restore the full feature cache or replay the holdout.
- The parallel branch reports three experiments/confirmation steps and a **HOLDOUT-DTI 0.0389** (95% CI 0.0282–0.0491; GEMSDOE32-HIDE-RECOVER-v3.0; 22,232 withheld positive instances) versus a fold-local parent proxy at 0.0992. Archived fold totals reproduce the arithmetic, but the predictions and intervals were not independently replayed, the comparator did not refill, and the novelty stop was bypassed. Treat the budget as spent; do not rerun or promote AP-1. [Byte audit](evidence/parallel_ap1_audit.json) · [current negative run card](docs/data/run-card.json).
- A reproducible exact-pixel audit of the nine historical TIFFs and a lattice witness is available. The nine files are **not unique** under the literal 70% rule. The lattice geometry makes the commonly used 37,654-dot budget impossible under that rule on the mirror footprint. This is not a score.
- The accessible owner mirror called `sample_submission.tif` is **not authenticated** and contains the mirrored label values instead of all-absence predictions described by the official page. It is used only for explicitly limited forensics.
- The mandated GEMSDOE24 shared-tool pins were restored **read-only** for analysis. A parallel branch also committed GEMSDOE32 snapshots as legacy references; those are not proof that the mandated shared cache/evaluator are available, and must not become a private fork. Their upstream template is read-only to this account; a reproducible validator-label ambiguity is documented rather than privately patched, and [raised with the canonical maintainers](https://github.com/buffedlizard55-lab/GEMSDOE24/issues/74).
- The [GitHub Pages decision desk](docs/index.html) and [submission guide](docs/executive-summary.html) are static. The page checks public GitHub HEAD freshness in the browser; it does **not** silently update scores or approve uploads.

## Reproduce this run (no submission or model training)

Requirements: Python 3.11, `gh` with access to public GitHub, and package access to install dependencies. Large raster inputs and shared code are ignored by Git; input hashes are pinned.

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/fetch_audit_data.py        # 9 historical TIFFs, mirror sample/labels, one witness
.venv/bin/python scripts/restore_shared_tools.py    # pinned read-only subset; not a complete runnable template
.venv/bin/python scripts/audit_history.py
.venv/bin/python scripts/audit_parallel_ap1.py       # saved bytes and reported-fold arithmetic only
.venv/bin/python scripts/audit_shared_validator.py
.venv/bin/python scripts/build_scorecard.py
.venv/bin/pytest -q
node --test tests/js/source_freshness.test.cjs
```

The read-only [CI workflow](.github/workflows/audit.yml) fetches the pinned public audit inputs, replays the automated tests, and verifies generated pages; it does not train, update score claims or submit.

`python scripts/refresh_source_heads.py` updates only the public GitHub HEAD snapshot; it does not update scores or validate new files. For a future candidate, `scripts/validate_raster.py <file.tif> --template <authenticated-sample.tif>` runs a conservative independent **format diagnostic**; it never authorizes upload or proves the template authentic. The stricter whole-array finite diagnostic is a project guard, not an official requirement; the official text permits null/NaN outside bounds. Read the [submission guide](docs/executive-summary.html) and [executive review](docs/EXECUTIVE_REVIEW.md) for the unresolved contradiction and source links.

## Next steps

Obtain the actual assigned method lane, canonical cache and tools, the authentic organizer sample and data, and a complete current registry through authorized channels. Reconcile the lattice policy **without silently exempting it or gaming holes**; until then obey the literal stop. Fix the documented ambiguity once in the shared template with the maintainer. Only under a newly authorized budget, evaluate the assigned lane against a comparable incumbent with canaries, buffered folds and uncertainty before any separate slot selection. Do not store credentials, private training data, or large derived rasters in Git.
