---
name: vehicle-safety-defect-review
description: Review vehicle incident and complaint packets for potential safety defect
  signals and escalation evidence.
when_to_use: 'Pipeline kind: review.'
---

# Vehicle Safety Defect review pipeline

End-to-end vehicle safety defect review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review vehicle incident and complaint packets for potential safety defect signals and escalation evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-vehicle-safety-defect-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-vehicle-safety-defect-retrieval-policy`
5. **review_harness** — `harness` → `harness/vehicle-safety-defect-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/vehicle-safety-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/vehicle-safety-defect-frameworks`
- **rule_packs**: `rule-pack/grep-vehicle-safety-defect-flags`, `rule-pack/rag-vehicle-safety-defect-retrieval-policy`

## Success criteria

- rubric `rubric/vehicle-safety-defect-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/vehicle-safety-defect-review` v0.1.0
- License: `MIT`
- Industry: automotive, automotive.safety
- Full source manifest: see `references/manifest.yaml`
