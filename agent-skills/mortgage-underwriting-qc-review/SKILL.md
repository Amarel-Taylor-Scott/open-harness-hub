---
name: mortgage-underwriting-qc-review
description: Review mortgage files for income, asset, appraisal, fair-lending, and
  closing-condition evidence.
when_to_use: 'Pipeline kind: review.'
---

# Mortgage Underwriting QC review pipeline

Expanded mortgage underwriting qc review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review mortgage files for income, asset, appraisal, fair-lending, and closing-condition evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-mortgage-underwriting-qc-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-mortgage-underwriting-qc-retrieval-policy`
6. **review_harness** — `harness` → `harness/mortgage-underwriting-qc-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/mortgage-underwriting-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/mortgage-underwriting-qc-frameworks`
- **rule_packs**: `rule-pack/grep-mortgage-underwriting-qc-flags`, `rule-pack/rag-mortgage-underwriting-qc-retrieval-policy`

## Success criteria

- rubric `rubric/mortgage-underwriting-qc-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/mortgage-underwriting-qc-review` v0.1.0
- License: `MIT`
- Industry: finance, finance.lending
- Full source manifest: see `references/manifest.yaml`
