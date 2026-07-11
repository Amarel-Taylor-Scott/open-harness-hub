---
name: lab-result-critical-alert-review
description: Review lab critical-result workflows for notification timeliness, escalation,
  readback, and documentation.
when_to_use: 'Pipeline kind: review.'
---

# Lab Result Critical Alert review pipeline

Expanded lab result critical alert review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review lab critical-result workflows for notification timeliness, escalation, readback, and documentation.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-lab-result-critical-alert-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-lab-result-critical-alert-retrieval-policy`
6. **review_harness** — `harness` → `harness/lab-result-critical-alert-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/lab-critical-alert-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/lab-result-critical-alert-frameworks`
- **rule_packs**: `rule-pack/grep-lab-result-critical-alert-flags`, `rule-pack/rag-lab-result-critical-alert-retrieval-policy`

## Success criteria

- rubric `rubric/lab-result-critical-alert-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/lab-result-critical-alert-review` v0.1.0
- License: `MIT`
- Industry: healthcare.clinical, healthcare.public_health
- Full source manifest: see `references/manifest.yaml`
