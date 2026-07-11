---
name: auto-warranty-triage-review
description: Review warranty claims for coverage, repeat repair, field-quality signal,
  and fraud/evidence gaps.
when_to_use: 'Pipeline kind: review.'
---

# Auto Warranty Triage review pipeline

End-to-end auto warranty triage review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review warranty claims for coverage, repeat repair, field-quality signal, and fraud/evidence gaps.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-auto-warranty-triage-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-auto-warranty-triage-retrieval-policy`
5. **review_harness** — `harness` → `harness/auto-warranty-triage-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/auto-warranty-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/auto-warranty-triage-frameworks`
- **rule_packs**: `rule-pack/grep-auto-warranty-triage-flags`, `rule-pack/rag-auto-warranty-triage-retrieval-policy`

## Success criteria

- rubric `rubric/auto-warranty-triage-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/auto-warranty-triage-review` v0.1.0
- License: `MIT`
- Industry: automotive, automotive.warranty
- Full source manifest: see `references/manifest.yaml`
