---
name: procurement-bid-review-review
description: Review sourcing packets for bid fairness, evaluation criteria, conflict
  risk, and award documentation.
when_to_use: 'Pipeline kind: review.'
---

# Procurement Bid Review review pipeline

End-to-end procurement bid review review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review sourcing packets for bid fairness, evaluation criteria, conflict risk, and award documentation.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-procurement-bid-review-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-procurement-bid-review-retrieval-policy`
5. **review_harness** — `harness` → `harness/procurement-bid-review-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/procurement-bid-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/procurement-bid-review-frameworks`
- **rule_packs**: `rule-pack/grep-procurement-bid-review-flags`, `rule-pack/rag-procurement-bid-review-retrieval-policy`

## Success criteria

- rubric `rubric/procurement-bid-review-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/procurement-bid-review-review` v0.1.0
- License: `MIT`
- Industry: procurement, procurement.sourcing
- Full source manifest: see `references/manifest.yaml`
