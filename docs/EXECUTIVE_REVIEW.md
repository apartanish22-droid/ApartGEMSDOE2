# Executive review: GEMSDOE24/25/27/28/30/31/32/33/36

**Review scope:** repository contents and the submission/result information supplied in the task. **This is not a raster-level comparison or an independent confirmation of the listed scores.**

## Decision summary

**No submission TIFF is generated or authorized for download from this checkout.** The repository has documentation and a read-only format validator, but no competition data, cached features, reference rasters, canonical holdout/evaluation tools, writer, or candidate TIFF. A fabricated TIFF would not have verifiable competition CRS/shape/transform or calibrated predictions and could reproduce the reported `[0,1]` validation failure. It would be misleading to call one submission-ready.

**No score estimate is defensible.** There is no local spatial holdout dataset or evaluator. The numerical results below are transcribed from the user-provided prompt only. They are **USER-REPORTED, UNVERIFIED**—not HOLDOUT-DTI and not ORGANIZER-CONFIRMED. In particular, the prompt gives conflicting leaderboard context (`0.4413` and `0.3195`) as well as `0.2778` for GEMSDOE32. The current official leaderboard and submission-page receipts were not available in this checkout, so the conflict remains unresolved.

The requested lane paragraph is not present as an identifiable single method specification: the protocol refers to “the single method paragraph below,” but the supplied text contains multiple previous methods/results and no unambiguous sole method paragraph. In accordance with the parallel-run rule, no method was selected, no experiment was run, and no weekly submission slot should be used.

## Highest user-reported result by target site

“Best reported” below means only the highest score shown for that site in the prompt, not a validated recommendation. Since registry rasters and the candidate TIFFs are absent, pixelwise uniqueness is **UNKNOWN** for every row. Distinct names or methods do not establish distinct raster contents. “No” in the submit column means do not submit on the evidence currently available; it does not claim the original file is invalid.

| Site | Highest result stated in the prompt | Score status | File / uniqueness / submission decision |
|---|---|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` — 0.2477 | USER-REPORTED, UNVERIFIED | Raster download URL/content not checked; uniqueness UNKNOWN; **do not submit** based on this review. |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` — 0.2600 | USER-REPORTED, UNVERIFIED | Raster download URL/content not checked; uniqueness UNKNOWN; **do not submit**. |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` — 0.2449 | USER-REPORTED, UNVERIFIED | Raster download URL/content not checked; uniqueness UNKNOWN; **do not submit**. The prompt also reports later entries at 0.2190 and 0.2250; neither exceeds 0.2449. |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` — 0.2710 | USER-REPORTED, UNVERIFIED | Raster download URL/content not checked; uniqueness UNKNOWN; **do not submit**. The listed 0.2710 is slightly above the other listed 28 entries. |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` — 0.2600 | USER-REPORTED, UNVERIFIED | Raster download URL/content not checked; uniqueness UNKNOWN; **do not submit**. |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan` — 0.2708 | USER-REPORTED, UNVERIFIED | Raster download URL/content not checked; uniqueness UNKNOWN; **do not submit**. |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` — 0.2778 | USER-REPORTED, UNVERIFIED | This is the highest of the named sites in the supplied list. Raster content/uniqueness not checked; **do not submit**. |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` — 0.2632 | USER-REPORTED, UNVERIFIED | Raster download URL/content not checked; uniqueness UNKNOWN; **do not submit**. |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` — 0.2750 | USER-REPORTED, UNVERIFIED | Raster download URL/content not checked; uniqueness UNKNOWN; **do not submit**. |

The table is an executive index of the prompt's claims—not an endorsement, expected score, or ranking that implies transfer to a hidden test set. Scores from different experiments may be incomparable if their evaluator versions, data splits, or raster conventions differed.

## GEMSDOE32: what can and cannot be inferred

The prompt identifies the `h33-h33-2-b2-...-zeros` run at 0.2778 as the top of the nine named sites. Its filename suggests a particular experimental family and a “zeros” output convention, but a filename alone does not establish the algorithm, why it worked, or whether it was leakage-free. Without its method card, source code, input raster, holdout definition, score receipt, and comparison raster, a PhD-level causal explanation would be speculation.

It is **possible in principle** to beat a prior score, but this repository has no evidence that a new method does so. “Higher than 0.2778” can be claimed only after a comparable, leakage-resistant holdout experiment or an organizer receipt. The separate prompt values 0.3195 and 0.4413 are not used as estimates or verified current standings here.

## Hypothesis slate and experiment gate

The requested protocol assigns one method lane, limits the run to three experiments/two hours, requires a cached stack and canonical tools, and requires holdout validation before any slot is touched. The lane is ambiguous in the supplied prompt, and none of the required data/tools exist in this repository. Therefore the following are **research questions, not approved experiments**; they are not scored or claimed to be novel. Their signal layers must be confirmed in the feature-stack metadata and checked against prior methods before implementation.

| Priority (conditional) | Candidate physical question | Required layer and target signature | Why it could find uncatalogued structures | Distinction / risk / cost |
|---|---|---|---|---|
| 1 (low-cost screen) | Are persistent magnetic boundaries more informative when normalized for local field amplitude? | Airborne magnetic total-field-derived gradients/edge persistence at multiple scales. | A sharp, spatially continuous susceptibility boundary can mark a buried structure that is not expressed as a mapped surface fault; it must be spatially separated from known catalogued traces during evaluation. | Different from simple edge magnitude only if persistence/scale stability is tested; existing GEMSDOE30 is explicitly named as an edge method, so novelty is **not established**. Low–medium cost. |
| 2 (conditional) | Do radiometric gradients reveal alteration/contact corridors that are structurally aligned but not already mapped? | Available K, eTh, eU channels and ratios; robust local gradients/ratios, not raw intensity alone. | Hydrothermal alteration or juxtaposed lithologies may create linear radiometric contrasts along concealed structures; the same signature can be caused by non-fault lithologic contacts or surficial cover. | Radiometric fusion appears in the supplied prior list (GEMSDOE46), so this is not shown to be novel. Medium cost; requires verified bands and careful non-fault controls. |
| 3 (conditional) | Do coincident magnetic and radiometric breaks improve specificity over either alone? | Co-registered magnetic and radiometric feature channels; spatial concordance of independent edges. | Cross-sensor agreement can suppress single-sensor noise and highlight a structure that is not in the fault catalogue. | Prior fusion has been reported, making “fusion” alone not novel; a carefully specified concordance statistic would need proof of distinction. Medium cost. |
| 4 (conditional) | Are structural edges preferentially preserved at a particular topographic scale after removing broad relief? | DEM-derived curvature/terrain position plus the relevant geophysical layer; scale-selective residual lineaments. | A buried or subtle fault may produce a weak, scale-dependent geomorphic expression absent from the inventory. | Topographic/scarp/ridge methods are extensively represented in the prompt's prior list; high duplication risk. Medium–high cost. |

No winner is selected from this slate. In particular, the protocol prohibits choosing a submission here. First recover the missing single-lane method paragraph, actual feature-band inventory, and canonical evaluation artifacts. Then do the prescribed leakage canary and segment-buffered hide-and-recover evaluation for at most three experiments. If no candidate beats the existing comparable HOLDOUT-DTI best with uncertainty accounted for, record a negative result and do not create a slot candidate.

No external dataset is proposed as a viable dependency in this review: the potential signals above are conditional on layers already being present in the competition's cached feature stack. If a needed layer is absent, the exact source and access must be checked before promoting that hypothesis; external network access was not available for that check in this repository review.

## Required next inputs and limitations

1. Restore or supply through the approved project mechanism: `training_features.tif`, `labels.tif`, `sample_submission.tif`, `existing_faults.tif` / registry rasters, and feature-band metadata. Do not commit private credentials or large data artifacts.
2. Restore the shared cached stack and canonical holdout evaluator/writer referenced in the protocol. The repository has a read-only TIFF format validator and synthetic tests, but no modeling scripts, cached features, canonical evaluator/writer, or CI configuration.
3. Provide the exact single method paragraph that defines this parallel session's lane, and the evaluator version plus the prior best comparable HOLDOUT-DTI with withheld-positive count and confidence interval.
4. For each listed site, obtain the actual TIFF and method record plus an organizer submission receipt if its score is to be treated as confirmed. A landing-page name and number do not permit a raster uniqueness check.
5. Before download is enabled, run the complete release gate from the README and save machine-readable validator output, raster SHA-256, registry correlation and dot overlap. Current uniqueness status is unknown, not “unique.”

### Unverified / conflicting claims to resolve

- The prompt reports both 0.3195 and 0.4413 as the current highest competition score, and also supplies the GEMSDOE32 score 0.2778. These may refer to different times or leaderboards, but no evidence in this checkout resolves that.
- Multiple listed submissions contain `nan` in their IDs; this suffix alone does not prove NaN values occur in a raster. They must be inspected directly.
- “Zeros”/“allfinite” suffixes are not proof of correct footprint, calibration, uniqueness, or submission acceptance.
- Several reported results are repeated in the prompt. Repetition is not independent corroboration.

## Sources supplied by the user

These are links supplied in the task for review. They were not fetched or independently checked during this repository-only review; they should therefore be treated as leads, not verified evidence.

- [DrivenData competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData competition about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [Competition rules / landing page](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Competition data page (login required per user report)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Competition leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DrivenData reference solution repository](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDawn survey information](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [Submission guidance PDF (NLR)](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS OpenEI project submission](https://gdr.openei.org/submissions/1391)
- [EPSG:32611 reference](https://epsg.io/32611)
- [Tversky index background](https://en.wikipedia.org/wiki/Tversky_index)

## Run card (this review; no experiment performed)

```json
{
  "hypothesis": "No experiment selected: the session's single-method lane is ambiguous and the required data/tools are absent.",
  "mechanism": "Not tested; no surface placement or holdout was run.",
  "named_non_fault_mimic": "Not evaluated; lithologic contacts, surficial cover, and non-tectonic topographic edges are plausible mimics for the conditional hypotheses above.",
  "holdout_dti": null,
  "holdout_ci_95": null,
  "evaluator_version": null,
  "withheld_positive_count": null,
  "correlation_overlap_vs_registry": "NOT TESTED — registry rasters/candidate raster unavailable.",
  "raster_sha256": null,
  "validator_output": "NOT RUN — no candidate TIFF or sample-submission raster; NaN/range/CRS/shape/transform are unverified.",
  "submission_name": null,
  "submission_note": null,
  "verdict": "negative"
}
```
