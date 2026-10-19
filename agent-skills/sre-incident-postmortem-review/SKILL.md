---
name: sre-incident-postmortem-review
description: Review incident postmortems for timeline accuracy, impact quantification,
  root cause, corrective actions, and recurrence controls.
when_to_use: 'Pipeline kind: review.'
---

# SRE Incident Postmortem review pipeline

End-to-end sre incident postmortem review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

## Task

Review incident postmortems for timeline accuracy, impact quantification, root cause, corrective actions, and recurrence controls.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-sre-incident-postmortem-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-sre-incident-postmortem-retrieval-policy`
5. **review_harness** — `harness` → `harness/sre-incident-postmortem-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/sre-postmortem-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/sre-incident-postmortem-frameworks`
- **rule_packs**: `rule-pack/grep-sre-incident-postmortem-flags`, `rule-pack/rag-sre-incident-postmortem-retrieval-policy`

## Success criteria

- rubric `rubric/sre-incident-postmortem-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/sre-incident-postmortem-review` v0.1.0
- License: `MIT`
- Industry: sre, sre.oncall, software.devops
- Full source manifest: see `references/manifest.yaml`
