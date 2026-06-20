---
name: last-mile-delivery-exceptions-review
description: Review delivery exceptions for proof-of-delivery quality, refund risk,
  carrier performance, and customer fairness.
when_to_use: 'Pipeline kind: review.'
---

# Last Mile Delivery Exceptions review pipeline

End-to-end last mile delivery exceptions review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review delivery exceptions for proof-of-delivery quality, refund risk, carrier performance, and customer fairness.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-last-mile-delivery-exceptions-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-last-mile-delivery-exceptions-retrieval-policy`
5. **review_harness** — `harness` → `harness/last-mile-delivery-exceptions-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/delivery-exception-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/last-mile-delivery-exceptions-frameworks`
- **rule_packs**: `rule-pack/grep-last-mile-delivery-exceptions-flags`, `rule-pack/rag-last-mile-delivery-exceptions-retrieval-policy`

## Success criteria

- rubric `rubric/last-mile-delivery-exceptions-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/last-mile-delivery-exceptions-review` v0.1.0
- License: `MIT`
- Industry: logistics.last_mile, retail.support
- Full source manifest: see `references/manifest.yaml`
