# What the archived GEMSDOE32 B2 file can—and cannot—explain

**The reported 0.2778 is user-reported and unverified.** No organizer
submission-page receipt in this checkout binds it to the archived bytes. The
actual hidden labels, public-score calculation for this file, and reason for
any score change are unavailable. There is no justified prediction of a new
file's leaderboard score.

## What the raster audit established

The pinned GEMSDOE32 B2 archive has SHA-256
`c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`
and **37,654** positive cells within the mirrored footprint. It is an exact
subset of the audited GEMSDOE31 dot set: **2,545** GEMSDOE31-only dots were
removed, all within two pixels of the mirrored catalogue. It is also a subset of
the audited GEMSDOE25 D2.8 support, with **6,436** GEMSDOE25-only dots. These
are geometrical observations, not organizer scores or proof of causation. The
linked archival variant may not be the byte-identical uploaded file for other
sites. See [the full independent audit](../../evidence/historical_audit.json).

## A plausible mechanism, not a measured explanation

The [published metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
uses a 300 m triangular kernel and pooled distance-weighted Tversky index with
α=0.2 and β=0.8. Nearby dots can compete for the maximum credit on the same
truth pixels while still adding false-positive mass; deleting a redundant dot
may improve the score. It can also reduce true-positive credit for a different
truth geometry. The direction of the actual change therefore cannot be known
without the hidden labels and matching receipts.

[Organizer staff](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4)
confirm that known faults are masked **pixel-exactly**, not buffered, and that
new truth may lie within 300 m of known traces. A flank dot near a known fault
can thus be penalized or rewarded according to proximity to *new* truth. It is
not valid to claim the 200 m collar is inherently free, universally optimal,
or responsible for the reported 0.2778.

The simple `k > 0.2 × DTI` break-even identity in the tested metric applies to
an isolated, single-truth-pixel addition with full incremental credit. It is
**not** a general rule for a partially covered or multiple-truth scene. Compare
actual marginal TP, FP and FN instead; see `tests/test_metric.py`.

## What could improve the result

A different, scientifically grounded detector might add previously missed
structures while controlling false-positive mass. The ranked
[research slate](../../research/hypotheses.md) lists candidate layers, mimics,
cost and data gates. None has been run in this review or proved unique across
all parallel work. A buffered whole-segment, visible-only holdout and an
independently comparable control are prerequisites for selection, not a
calibrated estimate of the hidden leaderboard.

The literal registry rule is a separate blocker: at **37,654** distinct dots,
only **6,649** mirrored-footprint cells lie outside a pinned lattice's
three-pixel neighborhood, so overlap must be at least **82.34%**, above 70%.
This counting bound is conditional on that witness and does not rule out every
smaller candidate. Do not move points into lattice holes merely to game it.
