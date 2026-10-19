---
name: workplace-safety-incident-review
description: Review workplace incident packets for hazard correction, injury response,
  witness evidence, and recurrence controls.
when_to_use: 'Pipeline kind: review.'
---

# Workplace Safety Incident review pipeline

End-to-end workplace safety incident review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review workplace incident packets for hazard correction, injury response, witness evidence, and recurrence controls.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-workplace-safety-incident-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-workplace-safety-incident-retrieval-policy`
5. **review_harness** — `harness` → `harness/workplace-safety-incident-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/workplace-safety-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/workplace-safety-incident-frameworks`
- **rule_packs**: `rule-pack/grep-workplace-safety-incident-flags`, `rule-pack/rag-workplace-safety-incident-retrieval-policy`

## Success criteria

- rubric `rubric/workplace-safety-incident-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/workplace-safety-incident-review` v0.1.0
- License: `MIT`
- Industry: facilities, facilities.workplace_safety, ehs.audit
- Full source manifest: see `references/manifest.yaml`
