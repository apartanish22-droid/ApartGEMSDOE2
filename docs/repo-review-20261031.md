# Repository review — 31 October 2026

## Executive decision

**NEGATIVE — no TIFF is approved for competition submission.** No new geological candidate was tested or generated in this review, no score estimate was made, no organizer receipt was obtained, and no weekly submission slot was used. The repository does contain an H-BLIND-CONDUIT *format demo* from a separate prior run; this review's independent audit found a serious footprint-mask error (details below), and it is explicitly **not** a competition submission. The conclusion is deliberate: current competition data and the prepared feature stack are absent from this checkout, the shared holdout/evaluator/writer are not verified for the requested protocol, the full registry is unavailable, and this prompt does not unambiguously assign a single geological method lane.

The project's landing page and submission guide still say that no file is approved. For this review, the word “current” means this checkout's locally checked state as of the timestamp in the run card; it is not a claim that external competition pages or old archived TIFFs are current.

## Focus-site executive comparison

These are the nine best entries reported in the prompt. Their numeric values are **USER-REPORTED / UNVERIFIED** (not `HOLDOUT-DTI` and not `ORGANIZER-CONFIRMED`); their association with exact bytes was not established by submission-page receipts. The archived raster comparison is pinned to the historical variants described in [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) and [`evidence/historical_audit.json`](../evidence/historical_audit.json). It does not prove that the current GitHub Pages artifacts at their changed source heads are the same bytes.

| Site | Prompt-reported best submission name | Prompt-reported value (unverified) | Estimate for a new submission | Unique among these nine archived variants? | Download / submit decision |
|---|---|---:|---|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | **Not estimable** | **No** — overlaps peer rasters above the 70% stop | No approved download; do not submit the archived file |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | **Not estimable** | **No** — overlaps peer rasters above the 70% stop | No approved download; do not submit the archived file |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | **Not estimable** | **No** — overlaps peer rasters above the 70% stop | No approved download; do not submit the archived file |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | **Not estimable** | **No** — overlaps peer rasters above the 70% stop | No approved download; do not submit the archived file |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | **Not estimable** | **No** — overlaps peer rasters above the 70% stop | No approved download; do not submit the archived file |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | **Not estimable** | **No** — overlaps peer rasters above the 70% stop | No approved download; do not submit the archived file |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | **Not estimable** | **No** — overlaps peer rasters above the 70% stop | No approved download; do not submit the archived file |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | **Not estimable** | **No** — overlaps peer rasters above the 70% stop | No approved download; do not submit the archived file |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | **Not estimable** | **No** — overlaps peer rasters above the 70% stop | No approved download; do not submit the archived file |

**Why no estimate?** The prompt's historic leaderboard results are observations reported by the user, not paired estimates for a new raster. A new candidate needs the specified whole-segment, buffered, leakage-safe holdout and confidence interval. No valid run was possible, so inventing a projected score—or calling a historical result a score estimate—would be misleading. The reproducible saved-byte audit reports all 72 directed site-to-site comparisons; every archived focus variant has at least one peer above the requested 70% proximity limit. See [`evidence/audit_nine_sites_20261030.json`](../evidence/audit_nine_sites_20261030.json) and the pinned-variant caveat above.

### Existing H-BLIND-CONDUIT format demo — not a submission

The integrated repository contains [`apartgemsdoe2-h-blind-conduit-radiometric-magnetic-curvature-25k-20261031T044226Z-c92314e1-zeros.tif`](downloads/apartgemsdoe2-h-blind-conduit-radiometric-magnetic-curvature-25k-20261031T044226Z-c92314e1-zeros.tif), SHA-256 `5c41d6382c113196c340d0edfadddc94b3618d145f2e8cfa39597c3da1509cff`. Its run card says **format-valid demo only**, `ok_to_submit: false`, and HOLDOUT-DTI / CI are null. The file is not published here as a recommended download.

Independent review compared its saved pixels to the finite mask of the repository's V4 NaN-outside raster (same CRS/shape/transform, 5,167,373 finite cells; this is an **owner-repository proxy**, not an organizer-authenticated sample). Only 9,013 of the demo's 25,000 positive cells fall inside that mask; **15,987 / 25,000 (63.948%) lie outside**. This directly reproduces the builder's mask bug: it selected an all-finite `-zeros.tif` as reference, then defined footprint as `np.isfinite(reference_array)`, which marked all 12,279,160 rectangular cells as footprint. See [`evidence/h_blind_conduit_footprint_audit_20261031.json`](../evidence/h_blind_conduit_footprint_audit_20261031.json). The precise official footprint remains unauthenticated here, so this is a strong owner-mirror format failure, not a claim of portal test results.

Code inspection also shows the named radiometric, magnetic and curvature “layers” are sinusoidal/radial functions of normalized pixel coordinates, not actual GeoDAWN/3DEP rasters. A catalogue mask is loaded only from optional `/tmp/gems32_archival.tif` with no pinned hash; that path was absent during this audit, and its presence during the earlier build cannot be established. Its recorded 0.00% overlap is only versus GEMSDOE32 B2; the required all-registry final-dot comparison and pre-placement surface correlation were not established. Therefore this TIFF is **not demonstrated unique**, scientifically grounded on the named layers, or submission-ready. Do not upload it or try to fix it by relocating dots.

The repository's separate 31 Oct executive summary records an official leaderboard page fetch over ranks 1–23 with #1 at 0.4544 and says the user-supplied 0.3195 is absent there. My independent automated fetch in this review failed; the committed feed therefore remains stale. Treat the 0.4544 as a dated public-page observation, not a file-bound receipt or a result revalidated in this review. See [`EXECUTIVE_SUMMARY_20261031.md`](EXECUTIVE_SUMMARY_20261031.md) and the stale/current distinction in [`docs/data/source_feed.json`](data/source_feed.json).

### GEMSDOE32's reported 0.2778

The repository's historical raster audit supports a geometric observation: the archived B2 dots are a reduced subset of the D2.8 support, with removed predictions concentrated near the owner-mirrored catalogue. Given a distance-weighted Tversky metric, removing redundant predictions can reduce false-positive mass when those predictions earn no additional truth credit. It can also remove true positives. This is a **plausible mechanism, not a causal explanation or a prediction**: the 0.2778 value was not tied to a verified file receipt here, and the hidden test labels are unavailable.

The public-source feed was refreshed at `2026-10-31T04:41:01Z`: GitHub API HEAD lookups succeeded for all nine named sites and each HEAD differs from the earlier 27 October snapshot. This establishes source movement only. It does **not** re-download/audit the newly referenced site files or update the historical score table. The official leaderboard request in this review failed with a TLS/SSL EOF; the automated feed therefore retains a 0.4544 observation last fetched at `2026-10-27T21:20:59Z` and correctly labels it **stale**. A separate same-day repository executive summary records a manual official-page fetch of ranks 1–23 with #1 at 0.4544 and states 0.3195 is absent from those rows; I could not independently reproduce that fetch. Treat 0.4544 as a dated public-page observation, not a current verified value here or a file-bound receipt. The user's 0.3195 figure is also unverified in this review. See [`docs/data/source_feed.json`](data/source_feed.json) and [`EXECUTIVE_SUMMARY_20261031.md`](EXECUTIVE_SUMMARY_20261031.md).

## Hypotheses before implementation

The repository already contains a ranked five-row slate with the requested layer, physical signature, missing-catalogue rationale, non-fault mimic, distinction from prior methods, effort and data-viability notes: [`docs/research/hypotheses_untried.md`](research/hypotheses_untried.md). Its four untried proposals are H–C1 (closed-claim proximity × radiometrics), H–C2 (shallow well/spring temperature × radiometrics), H–C3 (InSAR deformation), and H–C4 (depth-varying conductance). H–RAD is an already-run negative, not a fresh proposal. The slate's ranking is qualitative; it provides **no measured expected DTI improvement**. Data retrieval, complete area coverage and/or provenance are marked unverified, so none is declared viable here. The cited official starting points are the [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [DOE GDR / INGENIOUS submission 1391](https://gdr.openei.org/submissions/1391), and [USGS 3DEP](https://www.usgs.gov/3d-elevation-program); they were not freshly fetched in this review.

No slate candidate was selected or tested. The prompt says to stay in “the single method paragraph below,” but contains no unambiguous method paragraph or explicit lane assignment. In addition, preflight fails closed. Selecting a candidate anyway would violate the lane constraint; running an experiment on absent/unverified data and the unresolved shared protocol would violate the reuse and validation requirements. No weekly slot was used.

## Three review passes

### Pass 1 — inspect the checkout and evidence

- Confirmed branch `arena/7f3b004e-apartgemsdoe2`; initial working tree was clean.
- Read the README standing brief, the landing page, current submission guide, nine-site summary, candidate slate, preflight and protocol guard, and the saved source-feed code/data.
- Found a release/UI inconsistency: the archived H-SARPU run card was negative, but its subpage was titled “ready for selector review,” displayed “Download Validated,” and gave a concrete upload checklist. The archive's own literal lattice failure and invalid holdout caveat made those download instructions unsafe to present as actionable.
- During integration, inspected the separately generated H-BLIND-CONDUIT format demo and its builder. Its recorded full-grid footprint disagrees with the finite footprint proxy used by another repository raster; a byte-level check found 15,987 positive cells outside that proxy mask. The builder's synthetic feature and optional, unpinned mask logic are documented below.
- Confirmed `data/` contains only metadata/receipts and `.gitkeep`; `.cache/gems_data` is absent. Preflight reports all four current core rasters absent, the cached feature stack unverified/absent, all nine pinned shared assets unverified, an incomplete registry, no assigned lane, and no submission authorization.
- Rechecked the source feed rather than repeating its old “live” leaderboard value. The official leaderboard fetch failed; GitHub site-head API checks succeeded for 9/9 sites but show changed HEADs requiring a new file-level audit.

### Pass 2 — execute available checks and look for unsafe claims

- Installed the repository's validation requirements into ignored `.venv`; `.venv` is local-only and is not part of the deliverables.
- `.venv/bin/python -m pytest -q`: **203 passed, 9 skipped, 4 subtests passed** (65 Rasterio `PendingDeprecationWarning`s). Skips include unavailable data-dependent replay; unit-test success is not scientific validation.
- `node tests/feed_ui.cjs`: success, stale and failure states passed. `node --test tests/js/source_freshness.test.cjs`: **2 passed**.
- Corrected the H-SARPU page generator: the archived TIFF/ZIP remain downloadable only as explicitly labeled research artifacts, while its upload checklist is replaced with a fail-closed decision and gates for any future candidate. Added regression assertions for the negative labels and current review artifacts.
- `.venv/bin/python scripts/preflight.py`: **BLOCKED** (nonzero status by design). The report is saved at [`evidence/preflight.json`](../evidence/preflight.json).
- Rechecked links/claims in the prior executive summary: it already labels scores as unverified, estimates for new files as not estimable, and historical rasters do-not-submit. This review added no TIFF or score.
- Ran `scripts/refresh_feed.py`: current checked snapshot persisted; the public leaderboard is explicitly stale while nine GitHub HEADs are current. This is not a content audit.

### Pass 3 — requirement and risk reconciliation

- **Unique TIF:** none generated in this review. A prior H-BLIND-CONDUIT format demo exists, but its grid-wide mask misclassifies 15,987 positive cells as inside when they lie outside the repository's current finite-mask footprint proxy; it uses synthetic coordinate fields, has no holdout, and lacks full-registry uniqueness checks. It is not approved for submission. No candidate can be checked pre-placement and post-placement against the complete current registry.
- **Submission [0,1]/grid validator:** no new saved bytes exist to validate. The organizer-authenticated sample/template is absent, so the prior portal error cannot be diagnosed or “fixed” by clipping or changing nodata without evidence.
- **Holdout score / CI:** none. No HOLDOUT-DTI value was generated, and no leaderboard projection is reported.
- **External sources:** the report provides official manual-review links, but they were not re-fetched because this session's network did not return the official leaderboard, and the data sources' spatial coverage/retrieval has not been proven. The candidate slate correctly marks these unverified.
- **Slots:** zero used. A separate selector remains required after a validated holdout win and every release gate.
- **Current feed irregularity:** all nine tracked source HEADs changed relative to the 27 Oct snapshot, while the leaderboard fetch failed. Historical comparisons must not be represented as an audit of those newer source contents.

## Ranked next steps

1. Resolve the specific ambiguous lane instruction and agree which already-ranked proposal (if any) is in scope; do not treat this report as authorization to run one.
2. Obtain competition data through the authenticated organizer route and confirm their exact hashes and sample/template. Restore the feature stack and canonical shared tools, then resolve evaluator/writer/registry defects in the shared source, not a private fork.
3. Rebuild the full registry from changed source heads; audit exact saved bytes; have its maintainers resolve the 5-pixel lattice's conflict with the literal 70% rule rather than gaming or silently exempting it.
4. Establish and independently test the requested whole-segment + buffer holdout; ensure catalogue features are derived only from visible faults and visible faults are masked pixel-exactly. Run a standalone canary for each feature.
5. Only if a preregistered hypothesis clears pre-placement novelty, leakage and matched uncertainty-aware HOLDOUT-DTI gates, produce and validate the exact output bytes against the authenticated template. Keep the selector separate and respect the official current weekly cap.
6. Re-fetch the leaderboard and changed source pages in an allowed authenticated environment, show timestamps/failure states, and bind any score to its submission receipt and file hash.

## Protocol run card

The machine-readable card is [`evidence/repo_review_run_card_20261031.json`](../evidence/repo_review_run_card_20261031.json). It is a **negative repository-review card**, not an experiment card with a measured score: this review generated no candidate, so its own HOLDOUT-DTI, CI, output hash, registry comparisons and validator results are null. The pre-existing H-BLIND-CONDUIT demo's separate saved-byte audit is [`evidence/h_blind_conduit_footprint_audit_20261031.json`](../evidence/h_blind_conduit_footprint_audit_20261031.json).
