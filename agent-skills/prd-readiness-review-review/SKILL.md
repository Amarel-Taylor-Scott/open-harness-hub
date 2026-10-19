---
name: prd-readiness-review-review
description: Review product requirements documents for problem clarity, measurable
  outcomes, dependencies, risks, and launch readiness.
when_to_use: 'Pipeline kind: review.'
---

# PRD Readiness Review review pipeline

End-to-end prd readiness review review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review product requirements documents for problem clarity, measurable outcomes, dependencies, risks, and launch readiness.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-prd-readiness-review-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-prd-readiness-review-retrieval-policy`
5. **review_harness** — `harness` → `harness/prd-readiness-review-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/prd-readiness-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/prd-readiness-review-frameworks`
- **rule_packs**: `rule-pack/grep-prd-readiness-review-flags`, `rule-pack/rag-prd-readiness-review-retrieval-policy`

## Success criteria

- rubric `rubric/prd-readiness-review-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/prd-readiness-review-review` v0.1.0
- License: `MIT`
- Industry: product_management, product_management.prd
- Full source manifest: see `references/manifest.yaml`
