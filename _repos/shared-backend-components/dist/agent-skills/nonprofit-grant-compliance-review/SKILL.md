---
name: nonprofit-grant-compliance-review
description: Review nonprofit grant files for allowable costs, subrecipient monitoring,
  reporting deadlines, and restricted-fund controls.
when_to_use: 'Pipeline kind: review.'
---

# Nonprofit Grant Compliance review pipeline

End-to-end nonprofit grant compliance review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

## Task

Review nonprofit grant files for allowable costs, subrecipient monitoring, reporting deadlines, and restricted-fund controls.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-nonprofit-grant-compliance-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-nonprofit-grant-compliance-retrieval-policy`
5. **review_harness** — `harness` → `harness/nonprofit-grant-compliance-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/grant-compliance-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/nonprofit-grant-compliance-frameworks`
- **rule_packs**: `rule-pack/grep-nonprofit-grant-compliance-flags`, `rule-pack/rag-nonprofit-grant-compliance-retrieval-policy`

## Success criteria

- rubric `rubric/nonprofit-grant-compliance-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/nonprofit-grant-compliance-review` v0.1.0
- License: `MIT`
- Industry: nonprofit
- Full source manifest: see `references/manifest.yaml`
