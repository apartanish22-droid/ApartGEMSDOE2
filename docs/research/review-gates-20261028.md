# Repository review — 28 October 2026

## Decision

**No approved submission and no estimated organizer score.** No experiment or weekly slot was used in this review. Existing TIFFs are research-only: a different name or a valid value range does not establish uniqueness, predictive skill, or authorization. The protocol reserves selection for a separate step after the gates pass.

The prompt does not identify the promised single assigned method paragraph. The previous H-UDSR lane is documented in [its preregistration](../../knowledge/preregistration_udsr_20261027.md); it already reports three experiments. Do not silently assign it or start a fourth. The earlier report's claims are historical, not independently reproduced in this review.

## Evidence and limitations

* The [nine-site audit](../../evidence/historical_audit.json) compares archived rasters. The claimed GEMSDOE32 result of 0.2778 is **user-reported, not organizer-confirmed**; no receipt tying a file hash to that score is available. The audit reports that its archived B2 pixels equal D2.8 after a two-pixel catalogue collar is removed. Reducing near-catalogue predictions and spacing the rest may have reduced the false-positive penalty while retaining coverage; this is a plausible interpretation, not proof of the hidden-score cause. There is no evidence guaranteeing a higher hidden score.
* A previous [H-UDSR run card](../../evidence/apartgemsdoe2_run_card_20261027.json) reports **HOLDOUT-DTI 0.094698** (GEMSDOE32-HIDE-RECOVER-v3.0, 22,232 reported withheld positive instances, 95% CI [0.082240, 0.107307]); it also reports overlap with a registered lattice exceeding the protocol's 70% limit. This is not a leaderboard estimate and was not replayed here. The same card reports a fold-honest control of 0.099202; see its paired interval and assumptions. Repeated sampling may mean the instance count is not a distinct-positive count.
* In this checkout, the cached competition rasters and shared template assets are absent. [The restore receipt](../../data/restore_receipt.json) records an earlier environment, not present files. `python scripts/preflight.py` now verifies core hashes from current bytes. A match confirms an owner mirror, **not** organizer authenticity. The mirror's sample is already flagged as anomalous in [the executive review](../EXECUTIVE_REVIEW.md).
* The current environment permits outbound access only to GitHub, PyPI and npm hosts. Official competition data and some original data links therefore cannot be accessed directly here; authorization and provenance remain separate from matching mirror hashes. A GPU and ability to train have not been established.
* The older [five ranked hypotheses](../../knowledge/preregistration_udsr_20261027.md) are prior-session proposals, not a validated new lane. Their scientific and source-availability claims require independent verification; e.g. the OPERA proposal was blocked in that environment.

## Changes and three review passes

1. Identified that four legacy AP2/H-UDSR run and emission entry points bypassed the existing protocol guard. They now fail closed before work or writing artifacts, like the other guarded entry points.
2. Fixed the AP2 local format validator: derive the footprint using raster masks and finite values; reject masked footprint predictions, misaligned or invalid labels, non-GeoTIFF input, and infinite/out-of-range values. NaN remains permitted **only outside** the footprint in this local check. Results are explicitly local format checks, not portal acceptance or slot approval.
3. Added live core-file hash checks to preflight, regression tests, and reran the Python and JavaScript tests and site builds. These checks do not authenticate the template, establish full-registry completeness, or reproduce a holdout.

## Next steps

Obtain an authorized organizer template and inputs under the competition rules; verify provenance and inspect current data using preflight. Obtain the complete frozen registry and its scope, including whether the near-covering lattice is legitimately included; do not exclude it without an explicit protocol change. Establish a named lane, budget, leak-free fold definition and independently replay the prior best with matched emission/refill and defensible spatial uncertainty. Run feature canaries, both surface and final-dot uniqueness checks, and saved-byte format checks before any separate selector decision. The literal lattice rule may make typical dot budgets mathematically impossible; see [the audit](../../evidence/historical_audit.json), rather than optimizing dots into lattice holes.

Official references: [organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [competition problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), and [DOE GDR](https://gdr.openei.org/submissions/1391). Links other than GitHub were not independently accessible from this sandbox during this review.
