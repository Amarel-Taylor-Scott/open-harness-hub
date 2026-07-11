---
name: customer-escalation-quality-review
description: Review customer escalation handling for response quality, ownership,
  policy adherence, and recovery plan.
when_to_use: 'Pipeline kind: review.'
---

# Customer Escalation Quality review pipeline

End-to-end customer escalation quality review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review customer escalation handling for response quality, ownership, policy adherence, and recovery plan.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-customer-escalation-quality-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-customer-escalation-quality-retrieval-policy`
5. **review_harness** — `harness` → `harness/customer-escalation-quality-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/customer-escalation-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/customer-escalation-quality-frameworks`
- **rule_packs**: `rule-pack/grep-customer-escalation-quality-flags`, `rule-pack/rag-customer-escalation-quality-retrieval-policy`

## Success criteria

- rubric `rubric/customer-escalation-quality-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/customer-escalation-quality-review` v0.1.0
- License: `MIT`
- Industry: customer_success.escalation, retail.support
- Full source manifest: see `references/manifest.yaml`
