# Provenance of vendored shared tools

Protocol rule 2 says reuse, don't rebuild, and never keep a private fork. This repo has no
write access to the upstream template (different GitHub owner), so the canonical tools are
**vendored as pinned copies** with logic unchanged, from:

- Source: `buffedlizard55-lab/GEMSDOE32` @ `73485f27cf230af770167397c2b72cb9ce3b3f25`
- Copied 2026-10-27: `src/gems32/{__init__,grid,metric,features,holdout,emitter,submission,paths,detector,mdrc}.py`,
  `scripts/{restore_data,evaluate_holdout,submission_writer,build_features}.py`,
  `registry/data_manifest.json`, `registry/prepared_manifest_upstream.json`
- Competition data restored from the hashes in `data_manifest.json`
  (sources: `buffedlizard55-lab/GEMSDOE` @ `c0c06ac82178…`, `GEMSDOE24` @ `07345ea06049…` etc.,
  each file SHA-256-verified by `scripts/restore_data.py`).

Reference clones reviewed this session (HEAD at review time):

| Repo | HEAD |
|---|---|
| GEMSDOE24 | a73f9ffba29260cc7708e8e0557c84c5bea7d47b |
| GEMSDOE25 | 19b219f629440b9975b093f459c74e21a42476ca |
| GEMSDOE27 | 4f34228a9f39e99da592aa34fd835c96d1b693f5 |
| GEMSDOE28 | 4955e29c7b66503ba2178b25d356d713dc1bc534 |
| GEMSDOE30 | d21ddd9502f3c3911e8d77b8f1e6abfaadffc876 |
| GEMSDOE31 | 88ec212955353f7590e94b8ef2a9763ffa035d45 |
| GEMSDOE32 | 73485f27cf230af770167397c2b72cb9ce3b3f25 |
| GEMSDOE33 | 844f514819041c7be9efd345a24cf5cd70263f00 |
| GEMSDOE36 | 7edcc9b58e6ad0f88c6e6f5ee9218761a391769d |
| drivendataorg/gems-prize-reference-solution | aebe92f7c8a990f0e3443451b7a825d9afd6336b |

## Deviations from the pinned copies (complete list)

- **IR-AP2-01 — `submission.py` filename prefix.** Upstream hard-codes `gemsdoe32-` in output
  filenames, which mislabels artifacts produced by any other repo. Minimal fix here: a
  `prefix="gemsdoe32"` keyword (default preserves upstream behaviour bit-for-bit). This fix
  belongs upstream; it is flagged here because this repo cannot push to GEMSDOE32.
- **IR-AP2-02 — literal lattice uniqueness is vacuous.** Earlier repos fail-closed candidates
  because ~99% of any dotted set lies within 3 px of the synthetic `r13-lattice-s5` calibration
  raster (206,895 dots on a 5-px lattice). With a 5-px lattice, balls of radius 3 px cover
  essentially the whole footprint, so *every* dotted submission fails by construction. AP2
  excludes synthetic covering lattices from the uniqueness denominator, measures and reports
  the lattice overlap anyway, and keeps the ≤70% / |ρ|≤0.90 rule for all genuine geological
  rasters. See the preregistration §4-G3.

No other logic was changed. `git diff` against the upstream files at the pinned commit will show
only the IR-AP2-01 hunk.
