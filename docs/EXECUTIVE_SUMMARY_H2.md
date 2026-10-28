# H2 demonstration — corrected decision, 28 October 2026

> **DO NOT SUBMIT THE H2 FILE. OK TO SUBMIT: NO. Verdict: `negative`.**

The archived H2 raster was generated from seeded pseudo-features, not the
competition feature stack. It is not a geological prediction; no leakage
canary or holdout was run. Its earlier conditional-upload advice, uniqueness
claims and dot-count score projections are withdrawn. The original text remains
in Git history for provenance.

## Independent saved-byte recheck

The archived file has SHA-256
`5a6da02c45e8cc96399763c1eba4f95bddd781f0ff2223c9d9a7f1dc3e90a801`.
Against the **owner-mirrored**, not organizer-authenticated, sample:

- `nodata=0` masks **5,140,874 of 5,167,373** mirrored-footprint cells.
- Of **61,396** positive cells in the whole file, **26,499** are inside that
  footprint and **34,897** are outside it.
- **26,478 / 26,499 = 99.92%** of its inside dots are within three pixels of
  the pinned lattice; the literal limit is 70%. This single counterexample
  proves a failure, not a complete registry audit.
- Stored cells are finite and in `[0,1]`; that alone does not establish a valid
  footprint, organizer-template match or portal acceptance.

See the [machine-readable read-back](../evidence/h2_saved_byte_recheck_20261028.json),
[corrected H2 card](data/run_card_h2.json), and
[official format and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
The reported earlier portal rejection concerned an unavailable file, so these
findings do **not** establish its cause.

## Scientific status

The proposed real-data texture idea is distinct from the pseudo-feature demo,
but neither fault-detection utility nor all-registry novelty has been shown.
The checked-in prototype's actual feature construction does not establish the
claimed directional box-counting mechanism. Roads, shorelines, lithological
contacts and erosional texture are plausible non-fault mimics. See the
[corrected hypothesis note](../research/hypotheses_h2_fractal.md).

No new H2 file, competition submission, or score was produced in this review.
