---
name: facilities-maintenance-workorders-review
description: Review maintenance work orders for priority, safety impact, preventive
  maintenance gaps, vendor evidence, and closure quality.
when_to_use: 'Pipeline kind: review.'
---

# Facilities Maintenance Workorders review pipeline

End-to-end facilities maintenance workorders review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review maintenance work orders for priority, safety impact, preventive maintenance gaps, vendor evidence, and closure quality.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-facilities-maintenance-workorders-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-facilities-maintenance-workorders-retrieval-policy`
5. **review_harness** — `harness` → `harness/facilities-maintenance-workorders-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/facilities-maintenance-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/facilities-maintenance-workorders-frameworks`
- **rule_packs**: `rule-pack/grep-facilities-maintenance-workorders-flags`, `rule-pack/rag-facilities-maintenance-workorders-retrieval-policy`

## Success criteria

- rubric `rubric/facilities-maintenance-workorders-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/facilities-maintenance-workorders-review` v0.1.0
- License: `MIT`
- Industry: facilities.maintenance, infrastructure
- Full source manifest: see `references/manifest.yaml`
