---
name: public-health-outbreak-triage-review
description: Review outbreak reports for case definition, exposure, reporting, lab
  confirmation, and intervention gaps.
when_to_use: 'Pipeline kind: review.'
---

# Public Health Outbreak Triage review pipeline

Expanded public health outbreak triage review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review outbreak reports for case definition, exposure, reporting, lab confirmation, and intervention gaps.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-public-health-outbreak-triage-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-public-health-outbreak-triage-retrieval-policy`
6. **review_harness** — `harness` → `harness/public-health-outbreak-triage-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/outbreak-triage-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/public-health-outbreak-triage-frameworks`
- **rule_packs**: `rule-pack/grep-public-health-outbreak-triage-flags`, `rule-pack/rag-public-health-outbreak-triage-retrieval-policy`

## Success criteria

- rubric `rubric/public-health-outbreak-triage-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/public-health-outbreak-triage-review` v0.1.0
- License: `MIT`
- Industry: healthcare.public_health, government.regulatory
- Full source manifest: see `references/manifest.yaml`
