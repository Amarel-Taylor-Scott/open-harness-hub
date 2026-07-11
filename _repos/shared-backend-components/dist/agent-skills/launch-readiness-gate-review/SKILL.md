---
name: launch-readiness-gate-review
description: Review launch packets for support readiness, legal approvals, monitoring,
  rollback, and communications completeness.
when_to_use: 'Pipeline kind: review.'
---

# Launch Readiness Gate review pipeline

End-to-end launch readiness gate review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review launch packets for support readiness, legal approvals, monitoring, rollback, and communications completeness.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-launch-readiness-gate-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-launch-readiness-gate-retrieval-policy`
5. **review_harness** — `harness` → `harness/launch-readiness-gate-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/launch-readiness-manager
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/launch-readiness-gate-frameworks`
- **rule_packs**: `rule-pack/grep-launch-readiness-gate-flags`, `rule-pack/rag-launch-readiness-gate-retrieval-policy`

## Success criteria

- rubric `rubric/launch-readiness-gate-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/launch-readiness-gate-review` v0.1.0
- License: `MIT`
- Industry: product_management.launch, marketing_ops.claims
- Full source manifest: see `references/manifest.yaml`
