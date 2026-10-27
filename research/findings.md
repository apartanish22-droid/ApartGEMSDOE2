# Why the reported GEMSDOE32 result may have been strong — and what we can actually prove

## Evidence boundary

The highest of the nine values supplied in the prompt is **0.2778, USER-REPORTED / UNVERIFIED**, attributed to GEMSDOE32 H33-2-B2. The owner’s [site](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) likewise states that it lacks a submission-page receipt binding that value to the raster hash. The [organizer leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) is a separate public observation, not a receipt for this file. The hidden expert labels and portal scores for these exact bytes are unavailable. Therefore neither the underlying score nor a causal explanation can be independently established here.

What we *did* verify: immutable historical files, their SHA-256 digests, their aligned binary in-footprint dot supports, and the directional pixel distances in [`evidence/historical_audit.json`](../evidence/historical_audit.json). The grid, footprint and catalogue used for this forensic calculation are owner-mirrored, not authenticated against DrivenData. These are **GEOMETRY-AUDIT quantities**, not HOLDOUT-DTI or organizer scores:

- GEMSDOE32 has 37,654 positive pixels and is exactly a subset of the 40,199-pixel GEMSDOE31 archival support. The 2,545 removed pixels are all at Euclidean distance at most 2 pixels from the mirrored known catalogue.
- GEMSDOE25's archival support contains all of GEMSDOE32's, plus 6,436 pixels. GEMSDOE36's archival support contains all of GEMSDOE32's, plus 1,200 pixels. Similar geography is not proof that different filenames were submitted to the portal or received the supplied scores.
- All 72 directional comparisons of the nine pinned historical supports exceed the protocol's overlap limit for at least one reason; every site has a clear duplicate-stop against another focus-site raster. This is not a complete registry audit, and no pre-placement surface was available.

## Mechanism consistent with the metric, not proof of causation

The [organizer defines](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric) a triangular spatial kernel `k(d) = max(1 − d / 300 m, 0)`. For each withheld truth pixel, true-positive credit is the **maximum** nearby `p(x) k(d)`, not the sum of all nearby predictions. Each predicted pixel contributes false-positive mass weighted by its distance to the closest truth; false-negative mass is the uncredited remainder of each truth pixel. The distance-weighted Tversky index is

`DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw + epsilon)`.

This makes coverage and redundancy distinct: if one prediction already supplies the maximum credit for a nearby truth, another can add no further credit to that truth while still contributing false-positive mass. **Removing a redundant prediction can improve DTI without detecting a new fault.** That is a plausible explanation for parts of the historical family ladder, not a determination of the actual hidden-test outcome.

More precisely, let old components be `T = TPw`, `F = FPw`, `N = FNw`, and let removing predictions reduce TP by `τ ≥ 0` and FP by `φ ≥ 0`. Since `T + N` is the fixed count of truth pixels, `N` increases by `τ`. Ignoring only the fixed tiny denominator epsilon, the removal improves DTI exactly when

`0.2 T φ > τ [0.2 F + 0.8 (T + N)]`.

If no maximum truth credit is lost (`τ = 0`) and a positive FP penalty is removed (`φ > 0`, `T > 0`), DTI improves. But if removed dots had unique credit for hidden faults, `τ` can dominate and DTI can fall. The mirrored catalogue proximity of the removed dots does **not** reveal their distance to the organizer's hidden labels, nor the organizer's masking implementation. Consequently the supplied ranking is compatible with the pruning mechanism but does not prove it.

## Can a new file beat the reported value?

Possibly, but **not proven or estimable in this session**. The published hidden labels are expert-identified faults absent from an imperfect catalogue; a holdout made by hiding known, already-mapped components is a proxy with a different selection mechanism. Unmapped faults can have different visibility, size, cover, geography, and mapping bias. Without a validated cross-family calibration using file-bound organizer receipts, mapping a catalogue holdout value to a leaderboard estimate is not justified. The current run generated no surface, valid holdout, or candidate TIFF.

Promising tests must improve coverage of *new* faults, not just score the training catalogue. Compare an assigned hypothesis to a frozen same-evaluator best using pooled components and paired spatial-block intervals, with whole-segment buffering and feature reconstruction from visible faults only. A feature-only AUC above 0.90 is a warning; an AUC below that threshold is **not** a proof of no leakage. Pre-register thresholds and final selection to limit repeated-search bias. Fault predictions are not proof of geothermal vents, reservoir temperatures, or flow.

## Why the literal uniqueness gate stops a champion-sized experiment

The pinned 13GEMSDOE calibration lattice is a listed member of the shared registry snapshot. Independently measured on the mirrored footprint, its 3-pixel neighborhood covers 5,160,724 of 5,167,373 cells; `U = 6,649` cells remain outside. For any `K` distinct positive footprint cells, at most `U` can be outside that neighborhood, so at least `max(0, K − U)/K` must overlap. At the champion count `K = 37,654`, this is **82.34%**, above the user's 70% limit regardless of spatial placement. This geometry does not prove that every smaller candidate is impossible.

The lattice is a calibration control rather than a geological detector, so it makes the literal proximity rule a poor discriminator of geological similarity at this count. Nevertheless, the user specified **any registry raster**; silently excluding it or placing dots in its holes would violate the protocol. Resolve the policy/registry issue explicitly before a new lane is run, and continue to respect the specified stop rule until then.

## The sample-mirror irregularity

The owner-mirrored file named `sample_submission.tif` has 60,988 positive in-footprint pixels and is equal to the mirrored label raster at every in-footprint cell. The organizer [describes its sample](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format) as predicting total fault absence. We cannot determine why they differ. The mirror can only provisionally anchor a forensic grid/footprint; it must not be used as a label-free feature or presented as the authenticated official template. Restore and hash the actual authenticated sample before release.

The reported portal error cannot be diagnosed without the rejected bytes. Inspect raw and masked values, nodata metadata and the saved TIFF; check inside-footprint finite values in [0,1], the official outside null/NaN specification, grid metadata and portal receipt. All-finite zeros and NaN-outside variants have different local diagnostics; neither is proof of live portal acceptance.
