# Candidate hypothesis slate — 30 October 2026

**Status:** one candidate was implemented and measured (H-RIDGE3). The others are *not* implemented.
No estimate, holdout score or leaderboard value is claimed for any idea below.
Every "verified" statement cites a page fetched on 30 Oct 2026 (links in the table).
This slate is ranked by expected DTI improvement and implementation cost, with the **expected
improvements marked as unmeasured**, because no validated holdout exists in this repo yet.

## Ranked hypotheses

| Rank | Hypothesis, layers and physical signature | Why it could catch a fault missing from the catalogue | Named non-fault mimic | Difference from earlier repo work | Cost | Data viability (verified this session) | Status |
|---|---|---|---|---|---|---|---|
| 1 | **H-DRAIN — paired drainage/fan displacement.** Bare-earth DEM (USGS 3DEP 1 m, via the competition's `1m_DEM_links.csv`) plus competition `det_elev` / `det_elev_slope`. Signature: matching channel profiles offset by a consistent vector across a candidate break. | A degraded or buried scarp can still offset drainage or fan edges. This tests displacement, not just ridge strength. | Fluvial terrace erosion, alluvial-fan avulsion, road cuts, stream capture. | Repo has no paired-offset test; prior H-TRACE used line coherence only. | High (DEM tiling, profile matching) | The [GeoDAWN release page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) says the lidar was collected through the USGS 3DEP Program. The 1 m DEM tile list is the competition's `1m_DEM_links.csv`, which sits behind the login-walled DrivenData download. **3DEP tiles and the tile list were not reachable from this sandbox.** | Not implemented |
| 2 | **H-FLIGHT — flight-line-subset stability of aeromagnetic edges.** GeoDAWN line-level magnetics (USGS release, CC0): build independent line-subset grids and keep edges stable across subsets, with `tmi_vg` / `iso_grav_anom_hg` as context. | A persistent subsurface contrast beneath alluvium should survive line-subset resampling; leveling stripes should not. | Line-leveling and micro-leveling artifacts at 200 m (Area 1) and 400 m (Area 2) line spacing. | Repo's Gaussian/Hessian features use the gridded product only. | Medium–high | [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) (DOI 10.5066/P93LGLVQ) is CC0 and lists flight-line CSVs; line spacing 200 m / 400 m verified on that page. **Not reachable from this sandbox** (USGS download hosts are not on the allowlist). | Not implemented |
| 3 | **H-RIDGE3 — coincident ridge fusion (implemented).** Hessian linear-strength of `det_elev` (band 12), `tmi_vg` (band 9) and `iso_grav_anom_hg` (band 18), geometric mean, 3×3 crest NMS, top 37,654 pixels. Catalogue not used to build predictions. | Co-located topographic, magnetic-contact and gravity-contact linear structure should mark traces that are weak in any single layer. | Shorelines and benches, road/rail embankments, drainage incisions, flight-line stripes, lithologic contacts. | Distinct from H-MAG-EDGE×SLOPE (magnetic gradient × slope) by using three layers, Hessian ridge strength and crest selection. | Low (done) | Inputs are the owner-mirrored competition feature stack (hash-verified, **not organizer-authenticated**). | **Measured: negative.** Catalogue in-sample DTI 0.0462; AUC 0.555 (weak). Surface gate pass, dot gate fails only against the synthetic lattice. See `evidence/ridge3_run_card_20261030.json`. |
| 4 | **H-CHEM — across-boundary hydrochemical contrast.** INGENIOUS well/spring chemistry and temperatures on opposite sides of candidate basin-margin normals. | A barrier fault can separate fluid histories even where its trace is unmapped. | Mixing, lithologic variation, sampling depth and time, pumping. | The repo's H-UDSR uses point proximity and plumes; this needs paired cross-boundary comparisons. | Medium | [GDR INGENIOUS compilation](https://gdr.openei.org/submissions/1391) (DOI 10.15121/1881483) is CC BY 4.0 and lists the "Well and Spring Temperature and Chemistry" geodatabase (19.85 MB). **Not reachable from this sandbox**; spatial density and comparability not checked. | Not implemented |
| 5 | **H-MT — electrical conductance contrast across candidate faults.** USGS MT conductance maps (2–200 km depth) and `cond_surf` / `depth_to_base_surf` (competition bands 17 and 15). | Fault zones with fluid-filled damage can show lateral conductance changes. | Lithologic and clay-alteration conductors; regional conductance gradients. | Repo's H-DEPTH×COND uses the same surface bands with a different combination; this uses the MT depth ranges. | Medium | The GDR INGENIOUS page links the USGS MT data release (DOI 10.5066/P9TWT2LU). **Not checked for coverage or download in this sandbox.** | Not implemented |

## Required checks before any idea is called viable

1. Obtain the exact file from its official source on a machine with access, and record its SHA-256.
2. Confirm spatial coverage of the 100 m grid (EPSG:32611).
3. Run per-feature leakage canaries (AUC > 0.90 means leakage until disproved).
4. Build a whole-segment, buffered holdout (1.5 km buffer per the repo protocol) and check that catalogue features are derived only from visible faults.
5. Run the surface gate (|ρ| ≤ 0.90) and dot gate (≤ 70% within 3 px) against **every** registry raster before placement and on the final dots.

## What this slate does not show

- No idea here is shown to beat the user-reported 0.2778 (GEMSDOE32). That number has no organizer receipt.
- No new expected improvement is claimed in DTI points for any idea. All improvements remain unmeasured.
