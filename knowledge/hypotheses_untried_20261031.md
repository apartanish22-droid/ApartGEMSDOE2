# Untried geological hypothesis slate — 31 October 2026

Status: proposals only. No holdout estimate, leaderboard value, or novelty claim is made for any idea
until it is validated. Ranking is by expected DTI improvement per implementation cost, following the
slate conventions in knowledge/candidate_slate_20261030.md and knowledge/preregistration-*.md. Every
single feature must pass the leakage canary (single-feature rank AUC vs holdout truth <= 0.90, else
leakage until disproved) before combination. All catalogue-derived features are built only from
fold-visible faults; whole fault segments are withheld with a 1.5 km (15 px) collar.

## Rank 1 (implemented in this session): H-DIL-GRAV
Layers: training_features band 8 `geod_dilaterate` (GPS/InSAR volumetric strain rate) and band 13
`iso_grav_anom` (isostatic gravity anomaly).
Signature: positive dilatation rate coincident with a negative gravity anomaly, both robustly
normalized to [0,1] and multiplied: belief = dil_norm × (−grav)_norm. Masked to the competition
footprint; non-finite cells get zero belief.
Why it may catch a catalogue-missing fault: concealed Great Basin normal faults localize dilatation
(permeability-opening damage zones) and hydrothermal alteration lowers bulk density (gravity low);
the co-located pair marks a concealed fault-controlled upflow zone that need not break the surface as
a mapped scarp — precisely the fault class missing from the USGS/INGENIOUS surface catalogue.
Named non-fault mimic: broad sedimentary basins produce gravity lows without faults; regional
tectonic extension produces dilatation without a discrete fault. Tested by checking each layer alone
on the holdout (canary) and by the spatial holdout itself.
Differs from prior repo work: H1 used radiometric × DEM curvature (surface-expression dependent);
dotted-ridge/scamp families detect edge strength; AP-1 used strain × conductance × gravity-edge as a
four-way rank product; H-DIL-GRAV is a two-layer, gravity-core mechanism with no surface scarp
requirement and no catalogue channel.
Cost: low (bands already in the restored 19-band stack; gradient-free).
Data viability: verified — training_features.tif bands 8 and 13 restored hash-verified from the
owner mirror (not organizer-authenticated); no new external download required.

## Rank 2: H-MAG-EDGE×SLOPE
Layers: band 3 `tmi_hg` (TMI horizontal gradient magnitude) and band 19 `det_elev_slope`.
Signature: strong magnetic edge coincident with steep residual topography.
Why: a fault displacing magnetic basement makes a gradient edge; steep detrended DEM marks a scarp
that may be alluvium-buried and unmapped.
Mimic: lithologic/volcanic contacts, erosion scarps.
Differs: multiplies magnetic edge by slope, so flat alluvium-covered scarps are suppressed unless
magnetic; distinct from H1 (no radiometric/DEM-curvature).
Cost: low (restored bands).
Data viability: verified (restored bands). Not implemented in this session.

## Rank 3: H-DEPTH×COND
Layers: band 15 `depth_to_base_surf` and band 17 `cond_surf`.
Signature: conductive signature under thin sediment cover.
Why: a fault-related conductive fracture zone beneath thin cover can host geothermal upflow with no
catalogue surface expression.
Mimic: clay-rich/saline intervals, inversion artifacts.
Differs: uses depth-to-basement × surface conductivity, distinct from H-DIL-GRAV (no geodesy).
Cost: low (restored bands).
Data viability: verified. Not implemented in this session.

## Rank 4 (new, not on prior slates): H-TMI-UPCONT-RESIDUAL × COND
Layers: USGS GeoDAWN TMI minus TMI upward-continued 150 m (from `geodawn_extensions_u8.tif`,
DOI 10.5066/P93LGLVQ, CC0; mirrored under buffedlizard55-lab/GEMSDOE24) and band 17 `cond_surf`.
Signature: shallow magnetic-source residual (near-surface demagnetization along a concealed fault)
co-located with elevated surface conductance.
Why: upward continuation removes deep sources; the residual isolates shallow (fault-scale) magnetic
sources. A concealed fault with hydrothermal demagnetization + fluid conduction is missing from the
surface catalogue unless it breaches as a scarp.
Mimic: shallow volcanic/lithologic magnetic bodies; conductive near-surface layers without faults.
Differs from H-RAD-MAG-CONTRAST (which used raw-field gradient products): depth-decomposed residual
plus conductance; no surface expression required.
Cost: medium (requires fetching the mirrored GeoDAWN extension grid and resampling to the 100 m
competition grid — the mirror already claims exact grid alignment).
Data viability: mirror bytes exist (SHA-256 pinned in registry/data_manifest.json); not yet fetched
into this checkout. Verify GeoDAWN CC0 terms and exact coverage before use.

## Rank 5 (new, not on prior slates): H-GEODAWN-RATIO-EDGE
Layers: GeoDAWN radiometric ratios Th/K (adularia/potassic alteration proxy) and U/K + U/Th (radon/leakage proxy)
from `geodawn_extensions_u8.tif`.
Signature: gradient edges of co-located alteration-ratio anomalies target blind fault-controlled
fluid pathways without requiring surface rupture.
Mimic: lithologic K/eTh contrasts at formation boundaries.
Differs: radiometric RATIOS rather than raw fields or gradient products; alteration geochemistry is
the physical target, not structure strength.
Cost: medium (mirrored grid; fetch + gradient + edge combination).
Data viability: mirror bytes exist; not yet fetched. Verify CC0 terms.

## Mandatory pre-implementation checks (per parallel-run protocol)
1. Obtain exact file from official source; record SHA-256. (Mirror pins verify consistency, not
   organizer provenance.)
2. Confirm spatial coverage of the 100 m EPSG:32611 grid.
3. Per-feature leakage canary: AUC > 0.90 = leakage until disproved.
4. Whole-segment buffered holdout (1.5 km collar); catalogue features from visible faults only.
5. Surface gate |rho| <= 0.90 and final-dot gate <= 70% within 3 px vs every registry raster before
   placement and on final dots.
6. Pooled HOLDOUT-DTI (alpha 0.2, beta 0.8, 300 m triangular kernel) + spatial 95% CI vs frozen
   same-protocol incumbent; paired uncertainty-aware comparison before any slot.

Links for manual review:
- Problem page/metric: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Official rules: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- USGS GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and (DOI 10.5066/P93LGLVQ, CC0)
- DOE GDR #1391 INGENIOUS: https://gdr.openei.org/submissions/1391 (DOI 10.15121/1881483, CC BY 4.0)
