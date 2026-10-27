# Evidence interpretation

The [current negative run card](../docs/data/run-card.json) and
[parallel AP-1 byte audit](parallel_ap1_audit.json) are the current decision.
`experiment_exp1.json`, `experiment_exp2.json`, `run_card_final.json`,
`validator_final.json` and the receipts in `docs/downloads/` are retained as
**historical parallel-session records**, not independent replays or authorizations.
The old final card's focus-nine-only uniqueness check omitted the lattice even
though its own overlap report exceeded 70%; the user did not authorize this
exception. Its `format_validator_*` flags do not authenticate the mirror template
or determine organizer acceptance. Do not submit any of those files.

`history_manifest.json` and `history_audit.json` pin and compare the nine
historical files plus the lattice, but do not represent a complete registry.
