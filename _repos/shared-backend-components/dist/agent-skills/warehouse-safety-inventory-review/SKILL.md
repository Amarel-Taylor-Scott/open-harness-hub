---
name: warehouse-safety-inventory-review
description: Review warehouse incident and inventory-control packets for safety hazards,
  shrink, cycle-count gaps, and remediation.
when_to_use: 'Pipeline kind: review.'
---

# Warehouse Safety Inventory review pipeline

End-to-end warehouse safety inventory review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review warehouse incident and inventory-control packets for safety hazards, shrink, cycle-count gaps, and remediation.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-warehouse-safety-inventory-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-warehouse-safety-inventory-retrieval-policy`
5. **review_harness** — `harness` → `harness/warehouse-safety-inventory-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/warehouse-ops-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/warehouse-safety-inventory-frameworks`
- **rule_packs**: `rule-pack/grep-warehouse-safety-inventory-flags`, `rule-pack/rag-warehouse-safety-inventory-retrieval-policy`

## Success criteria

- rubric `rubric/warehouse-safety-inventory-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/warehouse-safety-inventory-review` v0.1.0
- License: `MIT`
- Industry: logistics, logistics.warehouse
- Full source manifest: see `references/manifest.yaml`
