# Standing project brief

This is a durable, consolidated copy of the user's operational request; duplicate paragraphs and the long historical score list are not represented as independent evidence. Read it with the [README](../README.md) every session.

## Outcome and user experience

- Work autonomously and in multiple review passes. Prioritize the highest scoring submissions from GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36. For each, provide an executive comparison, the actual file or source, a responsibly labeled result or estimate, uniqueness status, and an obvious submit/do-not-submit decision.
- Produce an independently generated, scientifically defensible, unique competition TIFF and make it easy to download **only when all gates pass**. Never rename or copy an old file and represent it as a novel submission. Do not claim a hidden leaderboard score from an uncalibrated projection.
- Investigate the owner-reported GEMSDOE32 0.2778 result; distinguish verified raster geometry and metric mechanisms from unknown causation and unverified scores. Explore plausible improvements without promising a score above 0.2778, 0.3195, 0.4413, or any changing leaderboard leader.
- Create a clean GitHub Pages site with an executive submission guide, a readable source table and automated validation; make current status and download permissions immediately obvious. Preserve transparent source timestamps and never call a stale snapshot a live feed. Capture a unique name, ≤140-character note, SHA-256, and machine-readable run card for any actual candidate.
- Explain access, data, scientific, competition and deployment limitations. Cite official verified sources; distinguish public owner claims, official public leaderboard snapshots, submission-page receipts, holdout metrics, geometry diagnostics and projections. No fabricated facts, scores, receipts or validations.

## Parallel-run and scientific protocol

1. Follow only the explicitly assigned method lane. Compare surface before dot placement and final dots against every registry raster: stop if rank correlation is above 0.90 or more than 70% of dots are within three pixels of one registry raster. Do not silently exempt the calibration lattice or manufacture a pass.
2. Reuse the canonical cache, evaluator and writer; correct a shared defect once in its canonical template rather than maintaining a private fork. Hold out whole fault segments with a buffer; construct every catalogue-based feature solely from visible faults; mask visible known-fault pixels exactly. Pool DTI with alpha 0.2, beta 0.8, 300 m triangular kernel.
3. Check every feature independently for leakage; AUC above 0.90 is suspicious until investigated. Every HOLDOUT-DTI must identify evaluator, withheld positives and 95% confidence interval; ORGANIZER-CONFIRMED means a submission-page receipt. An estimate is never a score.
4. Before modeling, rank three to five previously untried local hypotheses with exact layers, physical signature, reason they might detect uncatalogued faults, distinction from this repo's past work, named non-fault mimics, and cost. Where new external data is needed, identify an official free source and verify binary obtainability before calling the idea viable. Use at most three experiments or two hours; require a paired, uncertainty-aware win over the current same-evaluator holdout best. No weekly slot without a separate selector decision.
5. Validate saved TIFF bytes against an authenticated official template: one float32 band, EPSG:32611, matching shape/geotransform/bounds and footprint, finite `[0,1]` predictions inside; resolve the official null/NaN-exterior language versus the previously reported portal range error. Check both scientific novelty and identity; no manual image inspection substitutes for these checks.
6. Finish with one JSON run card including hypothesis, mechanism, named mimic, holdout DTI/CI, correlation and overlap, raster hash, no-NaN/range/grid validator output, submission name/note and `promote` or `negative` verdict. Negative work is useful evidence.

## Primary references

- [DrivenData problem, DTI, data and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/); [about](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/); [data (login required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/); [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
- [DOE/NLR official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf); [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).
- [USGS GeoDAWN magnetic/radiometric survey](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and); [INGENIOUS project](https://gbcge.org/current-projects/ingenious/); [DOE GDR compilation](https://gdr.openei.org/submissions/1391); [USGS 3DEP](https://www.usgs.gov/3d-elevation-program).
- The user supplied Dropbox links to a PDF, example submission, existing faults, numerical features and DEM links; the restricted shell could not retrieve their binaries. Do not interpret URL availability as byte authentication.

The user also requested a PR and merge to main after review. Do not spend competition slots while doing so.
