---
name: data-lineage-catalog-review
description: Review data catalog entries for ownership, lineage, freshness, classification,
  and usage context.
when_to_use: 'Pipeline kind: review.'
---

# Data Lineage Catalog review pipeline

End-to-end data lineage catalog review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review data catalog entries for ownership, lineage, freshness, classification, and usage context.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-data-lineage-catalog-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-data-lineage-catalog-retrieval-policy`
5. **review_harness** — `harness` → `harness/data-lineage-catalog-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/data-lineage-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/data-lineage-catalog-frameworks`
- **rule_packs**: `rule-pack/grep-data-lineage-catalog-flags`, `rule-pack/rag-data-lineage-catalog-retrieval-policy`

## Success criteria

- rubric `rubric/data-lineage-catalog-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/data-lineage-catalog-review` v0.1.0
- License: `MIT`
- Industry: data_governance.lineage, software.devops
- Full source manifest: see `references/manifest.yaml`
