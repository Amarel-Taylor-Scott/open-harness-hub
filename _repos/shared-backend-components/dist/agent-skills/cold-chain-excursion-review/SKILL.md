---
name: cold-chain-excursion-review
description: Review temperature excursion packets for product disposition, custody
  evidence, and corrective action.
when_to_use: 'Pipeline kind: review.'
---

# Cold Chain Excursion review pipeline

End-to-end cold chain excursion review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review temperature excursion packets for product disposition, custody evidence, and corrective action.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-cold-chain-excursion-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-cold-chain-excursion-retrieval-policy`
5. **review_harness** — `harness` → `harness/cold-chain-excursion-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/cold-chain-quality-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/cold-chain-excursion-frameworks`
- **rule_packs**: `rule-pack/grep-cold-chain-excursion-flags`, `rule-pack/rag-cold-chain-excursion-retrieval-policy`

## Success criteria

- rubric `rubric/cold-chain-excursion-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/cold-chain-excursion-review` v0.1.0
- License: `MIT`
- Industry: logistics.cold_chain, food.safety
- Full source manifest: see `references/manifest.yaml`
