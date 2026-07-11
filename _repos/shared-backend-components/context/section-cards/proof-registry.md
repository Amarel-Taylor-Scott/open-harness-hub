# Proof Registry — section card

Section: `proof_registry` (category: governance) · critical-path.

## Purpose

A green proof that nobody runs is worthless. The proof registry is the single list of every proof module the
flywheel ticks, so "is the system honest?" reduces to "did every registered proof pass?". It is the
forcing function behind the maturity matrix's "every critical-path section has a proof REGISTERED in the
flywheel" rule — a section cannot claim completeness with a proof that the registry never runs.

## Owner module

`scripts/baltor_flywheel.py` — the `PROOF_MODULES` list and the tick that runs them all. (This is a shared
manifest; the main agent registers new proofs here, including `check_documentation_coverage`.)

## Contracts

The registry maps each proof script path to a label; the maturity-matrix check
(`scripts/check_section_maturity_matrix.py`) cross-references it so every reference section's proof must be
registered.

## Proof scripts

`scripts/baltor_acceptance.py` (registered) — the stakeholder "does the product actually work?" smoke test
that runs the whole Baltor motion over both bundled corpora via the shipped engines.

## Commands

```bash
PYTHONPATH=. python3 scripts/baltor_acceptance.py --self-test
PYTHONPATH=. python3 scripts/check_section_maturity_matrix.py --self-test
```

## Limitations

The registry is a hand-maintained Python list; a new proof is only enforced once it is added there (this card
does NOT edit it). The flywheel tick runs proofs sequentially and offline by design.

## Opportunities

Auto-discover `check_*` proofs to flag any unregistered proof; cross-check that every matrix `proof_scripts`
entry is registered.
