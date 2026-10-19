---
name: pharma-pv-icsr-review
description: Review adverse-event intake packets for ICSR minimum criteria, seriousness,
  expectedness, causality, and reporting clock risk.
when_to_use: 'Pipeline kind: review.'
---

# Pharma PV ICSR review pipeline

End-to-end pharma pv icsr review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

## Task

Review adverse-event intake packets for ICSR minimum criteria, seriousness, expectedness, causality, and reporting clock risk.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-pharma-pv-icsr-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-pharma-pv-icsr-retrieval-policy`
5. **review_harness** — `harness` → `harness/pharma-pv-icsr-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/pharmacovigilance-case-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/pharma-pv-icsr-frameworks`
- **rule_packs**: `rule-pack/grep-pharma-pv-icsr-flags`, `rule-pack/rag-pharma-pv-icsr-retrieval-policy`

## Success criteria

- rubric `rubric/pharma-pv-icsr-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/pharma-pv-icsr-review` v0.1.0
- License: `MIT`
- Industry: pharma, pharma.pv, healthcare.pharmacy
- Full source manifest: see `references/manifest.yaml`
