---
name: telecom-outage-postmortem-review
description: Review telecom outage postmortems for customer impact, regulatory reporting,
  root cause, and corrective actions.
when_to_use: 'Pipeline kind: review.'
---

# Telecom Outage Postmortem review pipeline

Expanded telecom outage postmortem review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review telecom outage postmortems for customer impact, regulatory reporting, root cause, and corrective actions.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-telecom-outage-postmortem-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-telecom-outage-postmortem-retrieval-policy`
6. **review_harness** — `harness` → `harness/telecom-outage-postmortem-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/telecom-outage-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/telecom-outage-postmortem-frameworks`
- **rule_packs**: `rule-pack/grep-telecom-outage-postmortem-flags`, `rule-pack/rag-telecom-outage-postmortem-retrieval-policy`

## Success criteria

- rubric `rubric/telecom-outage-postmortem-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/telecom-outage-postmortem-review` v0.1.0
- License: `MIT`
- Industry: telecommunications.fcc, sre.oncall
- Full source manifest: see `references/manifest.yaml`
