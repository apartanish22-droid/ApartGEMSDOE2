# GEMSDOE32's reported 0.2778: what the evidence does—and does not—explain

**Correction, 28 October 2026:** the previously published explanation overstated the marginal-DTI algebra, assumed the loss of 6,436 dots changed false-positive mass by exactly 6,436, and presented an unverified score progression as causal evidence. Those claims are withdrawn. The hidden labels, a file-bound organizer receipt and the per-dot credits are unavailable. The archived source is still in Git history; [the independent geometry audit](../../evidence/historical_audit.json) and [detailed derivation](../../research/findings.md) are the basis for the statements below.

## What is known

- The exact name `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` and value **0.2778** are **USER-REPORTED / UNVERIFIED**. The owner-published archive matches a hash-pinned TIFF, but no submission-page receipt binds its bytes to that value.
- The official public [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) was observed on 28 October 2026 with rank 1 **0.4544** and rank 2 **0.3916**. This is an organizer-published snapshot, not a receipt for B2 or a guarantee of the current value. It shows only that a public leaderboard value exceeded the *reported* 0.2778, not why.
- Against the pinned **owner-mirrored** catalogue, B2 has 37,654 positive cells and its support is exactly the D2.8 support after removing cells within two pixels of that catalogue. Its support is also a subset of the pinned GEMSDOE31 support. Our nine-site audit replays the saved-byte geometry but does not authenticate the competition inputs or score-to-file associations.
- All nine audited archival dot sets exceed 70% within three pixels of at least one other focus-site reference. The larger shared registry is not completely restored; these are not pre-placement surface comparisons.

## A plausible mechanism, not proof

The organizer defines a [300 m triangular distance kernel and DTI](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric): for each truth pixel, only its best nearby prediction earns true-positive credit, while predictions can add false-positive mass. Thus a redundant prediction can be penalized without adding truth credit. Thinning or removing near-catalogue predictions **might** improve DTI if it removes more false-positive mass than true-positive credit, but can reduce DTI when it removes the best prediction for a hidden fault.

For binary predictions with fixed truth count `K = T + N`, let old components be `T = TPw`, `F = FPw`, and `N = FNw`. If deleting dots reduces TP by `τ ≥ 0` and FP by `φ ≥ 0`, DTI improves exactly when, ignoring only the fixed epsilon,

`0.2 T φ > τ [0.2 F + 0.8 K]`.

The actual `τ` and `φ` depend on unknown hidden truth. The number of deleted dots is **not** automatically the reduction in FP mass; dots may be within the kernel of truth and may jointly contribute maximum credit to multiple truth cells. A single-dot rule with a constant denominator cost is therefore not generally valid. Neither the B2 collar geometry nor the reported score ranking proves score causation.

## Can a new method beat it?

**Possibly, not established.** Recovering more undisclosed faults with fewer false positives could help, but a holdout of catalogue-mapped faults differs from the expert-hidden population. No independently validated mapping converts our local diagnostics into a leaderboard estimate, and the latest review ran no new geological experiment. In particular, [the split audit](../../evidence/shared_split_geometry_20261028.json) found that the archived `GEMSDOE32-HIDE-RECOVER-v3.0` implementation does not establish the requested whole-segment, 1.5 km truth-to-visible buffer. Prior reported HOLDOUT-DTI values are archived diagnostics, not valid evidence under that protocol.

[Four ranked geological hypotheses](../../knowledge/preregistration_review_20261028.md) propose new detection content, with specific layers, mechanisms, mimics, costs and unverified availability. All are untested and unassigned. A fresh lane would require a corrected canonical shared evaluator, authenticated original inputs, a complete hash-verified registry, a pre-placement surface check, per-feature leakage canaries, a matched buffered holdout with a positive paired interval, and a final-dot overlap check. No proposed method is authorized merely by appearing in the slate.

## Why the current stop rule is binding

A registered lattice has 5,160,724 of 5,167,373 mirrored-footprint cells within three pixels; only 6,649 lie outside. At 37,654 distinct dots, at least `(37,654 − 6,649) / 37,654 = 82.34%` must overlap—above the requested 70% limit. This conditional counting bound does not exclude every smaller candidate. It does not authorize silently omitting the lattice or deliberately choosing its uncovered holes.

The saved H-TRACE research TIFF independently overlaps that lattice by **22,406 / 22,438 = 99.857%** and therefore fails. Its reported 0.0893 HOLDOUT-DTI [0.0737, 0.1052] (archived evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld-positive occurrences) is not a validated buffered-holdout result and is not an organizer score. The [current run card](../../evidence/current_run_card.json) records the negative verdict, file hash, local format checks and limitations. **Do not submit it.**
