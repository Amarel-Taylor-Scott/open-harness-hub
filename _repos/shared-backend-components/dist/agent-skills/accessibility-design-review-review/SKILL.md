---
name: accessibility-design-review-review
description: Review product designs for accessibility risks, inclusive interaction
  patterns, and remediation evidence.
when_to_use: 'Pipeline kind: review.'
---

# Accessibility Design Review review pipeline

End-to-end accessibility design review review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review product designs for accessibility risks, inclusive interaction patterns, and remediation evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-accessibility-design-review-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-accessibility-design-review-retrieval-policy`
5. **review_harness** — `harness` → `harness/accessibility-design-review-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/accessibility-design-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/accessibility-design-review-frameworks`
- **rule_packs**: `rule-pack/grep-accessibility-design-review-flags`, `rule-pack/rag-accessibility-design-review-retrieval-policy`

## Success criteria

- rubric `rubric/accessibility-design-review-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/accessibility-design-review-review` v0.1.0
- License: `MIT`
- Industry: design_ops, design_ops.accessibility
- Full source manifest: see `references/manifest.yaml`
