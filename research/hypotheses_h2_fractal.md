# Archived H2 fractal proposal — not implemented or validated

**Status: proposal only; the saved H2 file is synthetic and must not be submitted.** Its [run card](../docs/data/run_card_h2.json) records seeded pseudo-features and no holdout DTI. The H2 generator entry point is permanently blocked; no new file is created by invoking it.

The old description overstated what was built. The real-data map builder in `src/generate_h2_fractal_submission.py` combines multiscale **gradients**, rather than calling its claimed box-counting and anisotropy helpers. The azimuth helper also needs independent review. Consequently neither the synthetic raster nor the existing real-data code demonstrates the proposed fractal/azimuthal method, its novelty, or its geological performance. Earlier unsupported score ranges, conditional-submit language, and claims of a portal-safe or fully unique file are withdrawn. Historical prose remains in Git history, not as current guidance.

## Scientific idea requiring a new, authorized lane

A possible future hypothesis is that multiscale, directionally coherent texture changes in elevation and geophysics may be associated with some fault zones, including covered basin margins. A lithological contact, volcanic flow boundary, alluvial-fan edge, road, or acquisition stripe can produce similar texture without fault displacement. The method would need a correctly implemented and independently tested scale- and orientation-sensitive statistic, authenticated data and verified coverage, comparison to existing repository methods, named leakage canaries, whole-segment-withheld spatial validation, complete registry comparisons, and a separate selector. At 100 m per pixel, a purported 50 m feature is below the raster sampling resolution; scale claims must respect the actual data.

No improvement magnitude or leaderboard score is estimable here. The hypothesis is not an assigned lane, and no new experiment is authorized solely by this page. The current qualitative alternatives are listed in [hypotheses.md](hypotheses.md), with official data-source and reuse caveats.
