---
name: education-accommodations-review
description: Review student accommodation packets for documented need, accessibility
  fit, privacy handling, and implementation accountability.
when_to_use: 'Pipeline kind: review.'
---

# Education Accommodations review pipeline

End-to-end education accommodations review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

## Task

Review student accommodation packets for documented need, accessibility fit, privacy handling, and implementation accountability.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-education-accommodations-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-education-accommodations-retrieval-policy`
5. **review_harness** — `harness` → `harness/education-accommodations-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/education-accessibility-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/education-accommodations-frameworks`
- **rule_packs**: `rule-pack/grep-education-accommodations-flags`, `rule-pack/rag-education-accommodations-retrieval-policy`

## Success criteria

- rubric `rubric/education-accommodations-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/education-accommodations-review` v0.1.0
- License: `MIT`
- Industry: education, education.higher, education.k12
- Full source manifest: see `references/manifest.yaml`
