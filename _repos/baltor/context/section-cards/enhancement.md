# Enhancement — section card

Section: `enhancement` (category: enhancement) · critical-path.

## Purpose

Enhancement turns verified context objects into a compact, consumable `context_pack` — and answers a direct
product question: *can we compress context WITHOUT depending on LLM summarization?* Yes. The compression
ladder runs the cheap, deterministic, auditable steps FIRST (dedupe, structure-preserving trims); an LLM is an
optional escalation at the very end, never the default. Every step preserves source handles, so nothing is
"enhanced" into being unattributable.

## Owner module

`_repos/shared-backend-components/scripts/context_compress.py` — the deterministic, non-LLM context compression ladder; composed by
`_repos/shared-backend-components/scripts/demo_full_app.py` in the full motion.

## Contracts

Input: `context_object`. Output: `context_pack` (`_repos/shared-backend-components/architecture/contract_registry.json#context_pack`).

## Proof scripts

`_repos/shared-backend-components/scripts/context_compress.py` (its own `--self-test`), `_repos/shared-backend-components/scripts/demo_full_app.py`, and
`_repos/shared-backend-components/scripts/baltor_acceptance.py` — all registered in the flywheel; the acceptance smoke test runs the whole
motion over both bundled corpora.

## Commands

```bash
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/context_compress.py --self-test
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/baltor_acceptance.py --self-test
```

## Limitations

The default ladder is deterministic and lexical/structural — it compresses safely but does not paraphrase. The
LLM escalation step is opt-in and goes through the gateway; it is not exercised on the offline correctness invariant.

## Opportunities

Wire a real compression provider (LLMLingua is the cataloged candidate) behind the optimization
`compression` slot; measure compression lift through the optimization harness rather than asserting it.
