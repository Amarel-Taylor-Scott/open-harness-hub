---
name: data-quality-incident-review
description: Review data quality incidents for lineage, blast radius, root cause,
  remediation, and consumer communication.
when_to_use: 'Pipeline kind: review.'
---

# Data Quality Incident review pipeline

End-to-end data quality incident review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review data quality incidents for lineage, blast radius, root cause, remediation, and consumer communication.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-data-quality-incident-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-data-quality-incident-retrieval-policy`
5. **review_harness** — `harness` → `harness/data-quality-incident-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/data-quality-incident-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/data-quality-incident-frameworks`
- **rule_packs**: `rule-pack/grep-data-quality-incident-flags`, `rule-pack/rag-data-quality-incident-retrieval-policy`

## Success criteria

- rubric `rubric/data-quality-incident-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/data-quality-incident-review` v0.1.0
- License: `MIT`
- Industry: data_governance, data_governance.quality
- Full source manifest: see `references/manifest.yaml`
