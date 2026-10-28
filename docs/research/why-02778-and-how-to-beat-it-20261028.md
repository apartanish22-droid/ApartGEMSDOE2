# GEMSDOE32's reported 0.2778: what the bytes show, and what remains unknown

**Updated 28 October 2026.** The value **0.2778 is USER-REPORTED / UNVERIFIED**: no organizer submission-page receipt connects it to the archived file's hash. The same qualification applies to the other eight supplied scores. The [official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) showed 0.4544 for its leader when checked on 28 October; that is a public leaderboard observation, not a file-bound receipt. It changes over time and does not establish a score for any file reviewed here.

## Verified relationships, not score causation

Using SHA-256-pinned archival variants and an **unauthenticated owner-mirrored** footprint and catalogue, the independent [historical audit](../../evidence/history_audit.json) finds:

- GEMSDOE25 and GEMSDOE30 have the same **44,090 positive dot locations** on the checked grid. Their GeoTIFF bytes and hashes are not identical.
- The archived GEMSDOE32 B2 raster contains **37,654 dots**, exactly the D2.8 locations after removing **6,436** locations at most two 100 m pixels from the mirrored catalogue. The archived B2 SHA-256 is `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`.
- All nine archived dot sets exceed 70% within three pixels of another focus-site raster. Their pre-placement surfaces and the complete external registry were not established. Different hashes alone do not demonstrate a unique geological method.

The association of a claimed score with any particular archived encoding is not established, nor is the effect of the deletion on hidden truth. The owner mirror is not an authenticated organizer template.

## Plausible scientific and scoring mechanisms

The [official metric description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) uses a distance-weighted Tversky index with α=0.2, β=0.8 and a 300 m linear distance weight. For binary predictions, spacing dots can reduce false-positive mass, but wider spacing can also reduce coverage of actual fault pixels. Whether the trade-off is favorable depends on the **private** expert-labeled truth and the full pattern of predictions; the user-reported numbers do not prove it was favorable here.

[DrivenData staff clarify](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) that known USGS/INGENIOUS fault pixels are excluded from evaluation. This does **not** say that a surrounding two-pixel collar is excluded, or that hidden faults do not occur near mapped faults. Pruning neighboring dots might reduce penalties if those dots were poorly supported, but could also remove useful coverage. Without the masked truth and actual component scores, it is not possible to attribute the reported difference to this operation, quantify its causal effect, or assume a nearby "dead zone."

## Can a unique approach beat 0.2778?

Possibly, but neither an improvement nor a numerical forecast can be justified from these data. The public leader's higher score demonstrates that a higher public **value** was attained; it does not validate this repo's method or prove why another participant scored as they did. A scientifically defensible attempt would test additional fault-sensitive information, withstand named non-fault mimics and survey artifacts, improve a matched spatially blocked holdout, and pass the literal full-registry gates before a separate selector considers a slot. See the [ranked proposal-only hypotheses](../../research/hypotheses.md).

The pinned spacing-5 lattice is an independent stop witness, not a score. On the mirrored footprint only 6,649 cells lie beyond three pixels from it. A distinct-dot budget above 22,163 necessarily exceeds 70% lattice overlap; minimum-spacing assumptions tighten that bound. The reproducible [lattice audit](../../evidence/lattice_bounds_20261028.json) gives exact conditions. These are necessary geometry bounds, not proof that any smaller, geological candidate is unique or effective, and not permission to game the rule by moving dots into edge holes.

No geological experiment was run in this review. Shared-tool defects are reported upstream at [registry audit #63](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/63) and [release gate #67](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/67); neither is represented as fixed here.
