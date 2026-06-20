---
name: retail-returns-abuse-review
description: Review retail return cases for policy compliance, customer fairness,
  fraud indicators, and escalation needs.
when_to_use: 'Pipeline kind: review.'
---

# Retail Returns Abuse review pipeline

End-to-end retail returns abuse review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

## Task

Review retail return cases for policy compliance, customer fairness, fraud indicators, and escalation needs.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-retail-returns-abuse-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-retail-returns-abuse-retrieval-policy`
5. **review_harness** — `harness` → `harness/retail-returns-abuse-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/returns-integrity-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/retail-returns-abuse-frameworks`
- **rule_packs**: `rule-pack/grep-retail-returns-abuse-flags`, `rule-pack/rag-retail-returns-abuse-retrieval-policy`

## Success criteria

- rubric `rubric/retail-returns-abuse-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/retail-returns-abuse-review` v0.1.0
- License: `MIT`
- Industry: retail, retail.support, security.fraud
- Full source manifest: see `references/manifest.yaml`
