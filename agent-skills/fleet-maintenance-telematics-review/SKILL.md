---
name: fleet-maintenance-telematics-review
description: Review fleet telematics and maintenance packets for overdue service,
  safety alerts, cost leakage, and downtime risk.
when_to_use: 'Pipeline kind: review.'
---

# Fleet Maintenance Telematics review pipeline

End-to-end fleet maintenance telematics review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review fleet telematics and maintenance packets for overdue service, safety alerts, cost leakage, and downtime risk.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-fleet-maintenance-telematics-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-fleet-maintenance-telematics-retrieval-policy`
5. **review_harness** — `harness` → `harness/fleet-maintenance-telematics-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/fleet-maintenance-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/fleet-maintenance-telematics-frameworks`
- **rule_packs**: `rule-pack/grep-fleet-maintenance-telematics-flags`, `rule-pack/rag-fleet-maintenance-telematics-retrieval-policy`

## Success criteria

- rubric `rubric/fleet-maintenance-telematics-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/fleet-maintenance-telematics-review` v0.1.0
- License: `MIT`
- Industry: automotive.fleet, transportation
- Full source manifest: see `references/manifest.yaml`
