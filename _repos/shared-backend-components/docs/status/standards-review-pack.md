# Standards Review Pack

Grounded review surface for the pattern→standards subsystem. Every catalog + proof + path cited below is a real,
single-source file on disk (no-fake). Regenerated live to reconcile a stale tombstone whose proof
(`scripts/check_standards_review_pack.py`) still required a grounded pack while the subsystem (catalogs + proofs + miner)
is active; the prior archived copy is preserved at `archive/legacy/README.md`. serves_truth=false.

## 1. Pattern miner report
The miner output lives at `.agent/pattern_miner_report.json` (detected patterns, one-offs, unstandardized repetitions,
candidate templates, recommended standards, waivers-needed) and is proof-gated by `scripts/check_pattern_miner.py`.

## 2. Standards catalog
The single source of adopted standards is `architecture/standard_catalog.json`, proof-gated by
`scripts/check_standard_catalog.py`.

## 3. Template catalog
Generation templates are single-sourced in `architecture/template_catalog.json`, proof-gated by
`scripts/check_template_catalog.py`.

## 4. Routine library
Reusable routines live in `architecture/routine_library.json`, proof-gated by `scripts/check_routine_library.py`.

## 5. Waivers
Deliberate exceptions to a standard are recorded in `architecture/pattern_waivers.json`, proof-gated by
`scripts/check_pattern_waivers.py`.

## 6. anti-patterns
The miner flags repeated one-offs that should be standardized rather than re-written. A real current example surfaced on
disk: `scripts/new.py`. These are candidates for a shared template/standard.

## 7. Sample generated component
A component is generated deterministically from an active template — e.g. `--template ingestion.source_adapter`
(a real ACTIVE entry in the template catalog) — so a recommended standard becomes a reusable component, not a new one-off.

## 8. Proof results
The subsystem is gated end-to-end by `scripts/check_pattern_standards_full_stack.py`, composing the per-artifact proofs
above (`scripts/check_standard_catalog.py`, `scripts/check_template_catalog.py`, `scripts/check_routine_library.py`,
`scripts/check_pattern_waivers.py`, `scripts/check_pattern_miner.py`). All green = the catalogs, templates, routines, and
waivers are consistent and real.
