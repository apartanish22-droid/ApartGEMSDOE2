# Source and data ledger

Reviewed 2026-10-27 UTC. Public page metadata can be reviewed via the links below; in this sandbox direct HTTP to non-GitHub hosts is blocked. A page listing a downloadable dataset is **not** proof that the exact bytes, study-area coverage, schema, or competition licence have been verified. Do not upload or redistribute competition data without checking the rules.

| Source | What it supports | Access/rights and current limitations |
|---|---|---|
| [DrivenData problem & metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Expert-mapped missing faults, features, distance-weighted Tversky (alpha 0.2, beta 0.8, 300 m), submission format | Public page reviewed. Hidden labels are not available. |
| [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Public team ranking | Public page observation is timestamped in `docs/data/source_feed.json`; it is not a file-bound submission receipt. |
| [DrivenData data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Organizer originals and sample template | Redirected to login in the page reader; no authenticated account or receipt in this session. Do not request credentials in chat. |
| [Official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Entry, PDF-stated three submissions per week, generative-AI narrative disclosure | Rules can change; current authenticated submission page determines the actual quota. |
| [Organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) | Baseline model and reproduction guidance | Public code; original challenge data are separate. |
| [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | Airborne magnetic/radiometric surveys, flight lines and positions; acquisition limitations | Public release marked CC0; exact line and grid bytes not retrieved here. |
| [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) | Free elevation products without use restrictions | Study-area tile availability and bytes not checked here. |
| [USGS Great Basin conductance maps](https://doi.org/10.5066/P9TWT2LU) | Five modeled depth-integrated conductance layers; depth ranges and file listing | Public ScienceBase page reviewed; exact bytes, alignment and rights for intended reuse still require verification. |
| [DOE GDR INGENIOUS 1391](https://gdr.openei.org/submissions/1391) | Regional geothermal, well/spring, fault, geodetic and other inputs | Public listing specifies CC BY 4.0; individual datasets may carry additional terms. Bytes/coverage not verified. |
| [USGS fault identification caveats](https://pubs.usgs.gov/mf-maps/mf1136/mf1136/limit.htm) | Topographic features may resemble faults for other reasons | Geologic caution; no support for a numerical performance claim. |
| [Pinned shared template](https://github.com/buffedlizard55-lab/GEMSDOE24/tree/2521cb676e172c141a4417e4925b73b6a896c1eb) | Existing shared holdout, writer, novelty code and registry snapshot | Owner-managed; read-only cached hashes verified. Selected files are not a complete executable checkout, cache or exhaustive current registry. |
| [Nine-site prior comparison](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/evidence/s23_focus_novelty.json) | Original pinned archival references and a prior comparison | Source inspiration, not organizer evidence; our independent exact-byte results are in `evidence/historical_audit.json`. |

**Mirror discrepancy:** `sample_submission.tif` and `labels.tif` fetched from an owner-supplied GitHub mirror are hash-pinned but not organizer-authenticated. The mirror sample contains catalogue positives, whereas the official page describes the sample as predicting total fault absence. Never call the mirror the original sample without independent verification.
