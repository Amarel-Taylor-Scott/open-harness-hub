---
name: sales-forecast-inspection-review
description: Review opportunity forecasts for stage hygiene, close-plan quality, risk
  flags, and commit confidence.
when_to_use: 'Pipeline kind: review.'
---

# Sales Forecast Inspection review pipeline

End-to-end sales forecast inspection review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review opportunity forecasts for stage hygiene, close-plan quality, risk flags, and commit confidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-sales-forecast-inspection-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-sales-forecast-inspection-retrieval-policy`
5. **review_harness** — `harness` → `harness/sales-forecast-inspection-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/sales-forecast-inspector
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/sales-forecast-inspection-frameworks`
- **rule_packs**: `rule-pack/grep-sales-forecast-inspection-flags`, `rule-pack/rag-sales-forecast-inspection-retrieval-policy`

## Success criteria

- rubric `rubric/sales-forecast-inspection-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/sales-forecast-inspection-review` v0.1.0
- License: `MIT`
- Industry: sales_ops, sales_ops.forecasting
- Full source manifest: see `references/manifest.yaml`
