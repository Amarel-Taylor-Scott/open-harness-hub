---
name: manufacturing-nc-capa-review
description: Review manufacturing nonconformance and CAPA packets for containment,
  root cause, corrective action, and verification evidence.
when_to_use: 'Pipeline kind: review.'
---

# Manufacturing NC CAPA review pipeline

End-to-end manufacturing nc capa review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

## Task

Review manufacturing nonconformance and CAPA packets for containment, root cause, corrective action, and verification evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-manufacturing-nc-capa-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-manufacturing-nc-capa-retrieval-policy`
5. **review_harness** — `harness` → `harness/manufacturing-nc-capa-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/manufacturing-quality-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/manufacturing-nc-capa-frameworks`
- **rule_packs**: `rule-pack/grep-manufacturing-nc-capa-flags`, `rule-pack/rag-manufacturing-nc-capa-retrieval-policy`

## Success criteria

- rubric `rubric/manufacturing-nc-capa-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/manufacturing-nc-capa-review` v0.1.0
- License: `MIT`
- Industry: manufacturing, manufacturing.qa
- Full source manifest: see `references/manifest.yaml`
