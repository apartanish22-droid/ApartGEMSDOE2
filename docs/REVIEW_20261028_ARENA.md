# Repository review — 28 October 2026

## Decision

**No new competition prediction, TIFF, score estimate, or submission approval was produced in this review.** The current checkout is blocked for a scientific run. No weekly slot was used. Existing TIFFs are research artifacts only.

The repo's forensic result for GEMSDOE32 is plausible but not a verified organizer score: **0.2778 is USER-REPORTED / UNVERIFIED**, with no submission-page receipt binding that value to a file hash. The archived GEMSDOE32 raster is reported to be a D2.8 support reduced from 44,090 to 37,654 dots by removing 6,436 locations within two pixels of the owner-mirrored catalogue. Given the competition's distance-weighted metric, removing prediction mass that adds little new hidden-truth credit could improve the score of that *same* support. This is a parsimonious metric explanation, not proof of causation, a new geological discovery, or a forecast. The nine-site analysis and file identities are in the [independent archival review](EXECUTIVE_REVIEW.md).

The prior repo reports a best **HOLDOUT-DTI 0.113696** (95% CI `[0.101306, 0.126712]`; evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`; 22,232 reported withheld-positive instances) for H-UDSR EXP-2. This result was **not independently replayed in this review** and is not a leaderboard estimate. The current preflight is `BLOCKED`, so there is no new HOLDOUT-DTI to compare with it.

## Pass 1 — inspect

Read the standing charter in [README](../README.md), project brief, executive pages, experiment/run-card records, data and template pins, validator code, and tests. Checked the actual workspace rather than historical restore receipts:

- `.cache/gems_data/` and `.cache/template-assets/` are absent. The machine-readable preflight reports the core rasters and all pinned shared-template files missing, no assigned lane, an incomplete registry, and no experiment authorization.
- The latest shared-tool review also flags that the pinned holdout applies a collar to quadrants rather than proving whole fault-segment withholding with the required truth-to-visible buffer (upstream [issue #60](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/60)); the registry audit may accept missing files or non-literal overlap ([issue #63](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/63)). Do not trust a pass until these shared-template defects are repaired and verified **in the template**, not a private fork. See the [shared holdout/registry review](research/review-mask-and-holdout-20261028.md).
- **8 Python tests are skipped** because the local competition cache, pinned references, or read-only shared template are absent. Historical receipts do not establish that these files are present now.
- Several public-source timestamps in the checked-in feed are older than the page's 24-hour freshness window. The UI appropriately marks source observations stale; the feed is not a live or current score guarantee.
- Found a serious H2 publication inconsistency: its top banner said not to submit, but the same page still offered a `curl` download, a positive download decision, and a dot-count-based projection. The H2 run card repeated withdrawn uniqueness/projection claims. The H2 command-line generator automatically fell back to seeded pseudo-features when data were absent, wrote into the public downloads directory, and described the method as fractal/anisotropic even though the production map uses a multi-scale Sobel-gradient proxy and does not call its box-counting or anisotropy functions.

## Pass 2 — correct and test

- Replaced the H2 summary with a correction-only, research-status page. It does not offer an upload/download action, score projection, uniqueness claim, or submission note.
- Rewrote the H2 run card so all unmeasured science/uniqueness/score fields are `null` or explicitly `not_run`; recorded the local saved-byte facts and the owner-mirror/footprint limitations.
- Replaced the mixed legacy status text with a short, unambiguous `DO NOT SUBMIT` status.
- Disabled the legacy H2 generator entry point before any output can be written. Preserved its source and raster for audit history; this did not fix the old algorithm or turn it into a supported method.
- Strengthened correction tests to prevent return of the unsafe download/projection language.
- Corrected wording that called H-TRACE “unique” when its final-dot audit failed the literal overlap gate. Byte-distinct is not geological or registry uniqueness.

### Read-only H2 artifact check

The stored H2 demo bytes were independently opened in this review. SHA-256 is `5a6da02c45e8cc96399763c1eba4f95bddd781f0ff2223c9d9a7f1dc3e90a801`; raster dimensions, CRS, transform, datatype, finite-value count, range, and nonzero-pixel count are recorded in [`docs/data/run_card_h2.json`](data/run_card_h2.json). All 12,279,160 demo-grid cells are finite and in `[0,1]`; the generator labels all cells as footprint, while the owner-mirror manifest reports 5,167,373 footprint cells. This is a **format/geometry diagnostic on a seeded demo**, not organizer-template validation, scientific performance, registry uniqueness, or portal acceptance. Its nonzero-pixel count is not a score.

## Pass 3 — rerun checks and reconcile

- Python: **144 passed, 8 skipped**, plus 4 unittest subtests. Skips are attributable to missing local competition/cache/reference inputs. The suite is not an independent scientific rerun.
- JavaScript source-freshness tests: **2 passed**; feed UI test passed.
- Python byte-compilation, local Markdown-link checks, and deterministic site/scorecard rebuild completed without errors or generated-file drift.
- The current preflight exits nonzero by design with status `BLOCKED`; no experiment or raster emission was authorized. The separate review run card is [`evidence/repo_review_run_card_20261028.json`](../evidence/repo_review_run_card_20261028.json).

## Candidate slate and experiment gate

The repo already records a four-idea [research slate](../research/hypotheses.md) and a five-item [parallel-session slate](../knowledge/preregistration_trace_20261028.md). These are proposals, not holdout results; global novelty across sibling sites is not established. A defensible next-session ranking is:

| Rank | Unimplemented-in-this-repo hypothesis | Candidate layers / targeted signature | Why it could find an unmapped fault; how it differs here | Expected HOLDOUT-DTI effect (qualitative only) | Cost / external data gate |
|---:|---|---|---|---|---|
| 1 | **Positive–unlabeled learning (H-PU)** | Competition's 19-band numeric feature stack plus fold-visible fault labels; target spatially coherent, multiband fault-like discontinuities in unlabeled corridors outside the visible-fault buffer, treating other uncatalogued pixels as unlabeled rather than reliable negatives. | Directly addresses catalogue incompleteness in the supervision target; changes the training objective rather than adding another ridge/trace transform. Not implemented in this checkout. Global novelty is unknown. Mimics include lithologic contacts and geophysical/flight-line artifacts. | **Potentially medium; high uncertainty.** No score or numerical lift is claimed. | **Medium.** Uses competition data only, but those authenticated inputs and the cached stack are absent; the DrivenData data page requires login and cannot be reached from this sandbox. Owner-mirror hashes do not authenticate the originals. |
| 2 | **Paired drainage displacement** | USGS 3DEP bare-earth DEM with competition detrended elevation/slope and isostatic-gravity gradient; paired cross-break channel/terrace profiles. | Tests offset geometry across a persistent structure rather than a single scarp or ridge. Could expose degraded basin-margin displacement away from mapped traces. Mimics: fan avulsion and terrace erosion. | **Potentially medium; uncertain.** | **High.** Requires area-specific DEM tiles and coverage validation from [USGS 3DEP](https://www.usgs.gov/3d-elevation-program); exact bytes/coverage were not fetched here, so it is not viable yet. |
| 3 | **Cross-depth conductance contrast** | Official Great Basin shallow/deep conductance products plus gravity gradient; compare aligned depth-integrated contrast across basin margins. | Targets a buried electrical boundary, not a surface lineament or the repo's updip posterior. Mimics: conductive clay/saline groundwater and inversion artifacts. | **Low-to-medium, highly scale-dependent.** | **Medium–high.** Needs exact rasters and resolution alignment from the [USGS ScienceBase release](https://doi.org/10.5066/P9TWT2LU); bytes and rights for this use were not checked, so it is not viable yet. |
| 4 | **Flight-line-stable magnetic edges** | GeoDAWN magnetic line measurements, locations/altitudes, and gridded magnetics; leave-flight-line-out edge stability at common height. | A real subsurface contact should persist across independent acquisition subsets; this is more than smoothing a finished grid. Mimics: lithologic contacts and residual leveling. | **Low-to-medium expected direct lift; likely value is artifact rejection.** | **High.** Requires actual official line data from [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and); the files and coverage were not fetched here, so it is not viable yet. |
| 5 | **Cross-margin fluid-chemistry contrast** | INGENIOUS well/spring chemistry and temperature with DEM/gravity; spatially blocked, uncertainty-weighted compositional contrast. | Tests a fluid-population boundary rather than proximity to known hot springs. Mimics: lithology and groundwater mixing without fault displacement. | **Unknown / potentially low; sparse and confounded observations are a major risk.** | **High.** Requires schema, coverage, dates and licence checks for [DOE GDR submission 1391](https://gdr.openei.org/submissions/1391); no bytes were obtained here, so it is not viable yet. |

These are **qualitative research priorities, not score projections**. No candidate was run or promoted in this review. The requested top-candidate validation is therefore still outstanding: it cannot be performed without the authenticated inputs, cached feature stack and assigned lane. Do not use a weekly slot. Restore only permitted data, verify source provenance, repair and verify the shared holdout/registry tools in the template (not a private fork), freeze the complete registry, then pre-register one lane and use the shared evaluator/writer with fold-visible catalogue features, whole-segment buffered holdouts, exact visible-fault masking, single-feature canaries, paired uncertainty, and both pre-placement and final-dot checks.

## Official-source and access limits

The repo links the organizer [problem/metric/format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), and [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution). In this environment, outbound access is limited to GitHub, PyPI, and npm; I could not freshly fetch or authenticate the non-GitHub organizer/USGS/GDR sources during this review. Links are provided for review, not described as newly verified. No hidden-label score or official receipt was accessed.

## Single JSON run card

This is the no-experiment review record; the identical machine-readable card is preserved at [`evidence/repo_review_run_card_20261028.json`](../evidence/repo_review_run_card_20261028.json). It records the prior HOLDOUT-DTI report separately from results not run in this review.

```json
{
  "schema": "parallel-run-protocol-run-card-v1",
  "record_type": "repository_review_no_experiment",
  "reviewed_at_utc": "2026-10-28T22:54:11Z",
  "hypothesis": null,
  "mechanism": null,
  "named_non_fault_mimic": null,
  "holdout_dti": {
    "label": "NOT RUN",
    "evaluator_version": null,
    "withheld_positive_instances": null,
    "ci95": [
      null,
      null
    ],
    "reason": "No method lane was explicitly assigned; local feature cache and shared template are absent. The pinned holdout also does not establish whole-segment buffered truth-to-visible withholding (upstream issue #60). Current preflight is BLOCKED."
  },
  "prior_reported_holdout_best": {
    "label": "HOLDOUT-DTI, historical repo report; not independently replayed in this review",
    "evaluator_version": "GEMSDOE32-HIDE-RECOVER-v3.0",
    "withheld_positive_instances": 22232,
    "point": 0.113696,
    "ci95": [
      0.101306,
      0.126712
    ],
    "candidate": "H-UDSR EXP-2",
    "note": "Not a leaderboard estimate. Current missing inputs prevent independent reproduction."
  },
  "registry_comparison": {
    "surface_rank_correlation": null,
    "final_dot_overlap_max": null,
    "candidate_raster_generated": false,
    "status": "not_run",
    "reason": "No new candidate surface or final dots were produced. The current complete registry is not verified."
  },
  "raster_sha256": null,
  "validator_output": {
    "new_candidate": null,
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null,
    "status": "No candidate raster was generated or validated in this review.",
    "legacy_h2_artifact": {
      "sha256": "5a6da02c45e8cc96399763c1eba4f95bddd781f0ff2223c9d9a7f1dc3e90a801",
      "single_band_float32_gtiff": true,
      "shape": [
        3730,
        3292
      ],
      "crs": "EPSG:32611",
      "transform": [
        100.0,
        0.0,
        243350.0,
        0.0,
        -100.0,
        4508550.0
      ],
      "all_array_pixels_finite": true,
      "all_array_values_in_0_1": true,
      "all_array_pixel_count": 12279160,
      "nonzero_pixel_count": 61396,
      "footprint_match_to_owner_mirror_manifest": false,
      "official_template_authenticated": false,
      "portal_acceptance": null,
      "scope": "Seeded synthetic DEMO bytes only; format statistics are not scientific or submission authorization."
    }
  },
  "submission_name": null,
  "submission_note": null,
  "submission_note_length_chars": null,
  "verdict": "negative",
  "experiments_run_this_review": 0,
  "prior_parallel_budget_reported_used": 3,
  "weekly_slots_used": 0,
  "preflight_status": "BLOCKED",
  "blockers": [
    "No explicitly user-assigned method paragraph/lane identified.",
    "Competition data cache, prepared feature stack, and pinned shared-template assets absent in current workspace.",
    "Historical restore receipt is not proof of current file availability or official provenance.",
    "Complete, current registry not verified.",
    "Previous parallel lane reports its three-experiment budget used; no experiment was authorized or performed in this review.",
    "No authenticated submission-format template or portal receipt available.",
    "Pinned holdout truth-to-visible geometry is not proven to hide whole fault segments with the required buffer (upstream issue #60); fix/verify the shared template, not a private fork.",
    "Shared registry audit may pass missing files or non-literal overlap (upstream issue #63); do not trust its pass flag until fixed/verified in the shared template."
  ],
  "review_artifact": "docs/REVIEW_20261028_ARENA.md"
}
```
