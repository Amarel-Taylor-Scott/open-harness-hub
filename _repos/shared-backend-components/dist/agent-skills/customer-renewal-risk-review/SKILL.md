---
name: customer-renewal-risk-review
description: Review account packets for renewal risk, value realization, adoption
  gaps, and escalation actions.
when_to_use: 'Pipeline kind: review.'
---

# Customer Renewal Risk review pipeline

End-to-end customer renewal risk review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review account packets for renewal risk, value realization, adoption gaps, and escalation actions.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-customer-renewal-risk-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-customer-renewal-risk-retrieval-policy`
5. **review_harness** — `harness` → `harness/customer-renewal-risk-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/renewal-risk-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/customer-renewal-risk-frameworks`
- **rule_packs**: `rule-pack/grep-customer-renewal-risk-flags`, `rule-pack/rag-customer-renewal-risk-retrieval-policy`

## Success criteria

- rubric `rubric/customer-renewal-risk-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/customer-renewal-risk-review` v0.1.0
- License: `MIT`
- Industry: customer_success, customer_success.renewal
- Full source manifest: see `references/manifest.yaml`
