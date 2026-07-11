---
name: hospitality-guest-safety-review
description: Review hospitality incident packets for guest safety, duty-of-care evidence,
  escalation, and remediation tracking.
when_to_use: 'Pipeline kind: review.'
---

# Hospitality Guest Safety review pipeline

End-to-end hospitality guest safety review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

## Task

Review hospitality incident packets for guest safety, duty-of-care evidence, escalation, and remediation tracking.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-hospitality-guest-safety-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-hospitality-guest-safety-retrieval-policy`
5. **review_harness** — `harness` → `harness/hospitality-guest-safety-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/hospitality-safety-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/hospitality-guest-safety-frameworks`
- **rule_packs**: `rule-pack/grep-hospitality-guest-safety-flags`, `rule-pack/rag-hospitality-guest-safety-retrieval-policy`

## Success criteria

- rubric `rubric/hospitality-guest-safety-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/hospitality-guest-safety-review` v0.1.0
- License: `MIT`
- Industry: hospitality
- Full source manifest: see `references/manifest.yaml`
