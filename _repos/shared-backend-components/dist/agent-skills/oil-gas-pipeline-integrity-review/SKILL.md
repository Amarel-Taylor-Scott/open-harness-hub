---
name: oil-gas-pipeline-integrity-review
description: Review pipeline integrity packets for anomaly severity, pressure restriction,
  excavation, corrosion, and repair evidence.
when_to_use: 'Pipeline kind: review.'
---

# Oil Gas Pipeline Integrity review pipeline

Benchmarkable oil gas pipeline integrity review pipeline with normalization, grep, RAG, harness review, severity calibration, evidence gaps, and risk-register output.

## Task

Review pipeline integrity packets for anomaly severity, pressure restriction, excavation, corrosion, and repair evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-oil-gas-pipeline-integrity-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-oil-gas-pipeline-integrity-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/oil-gas-pipeline-integrity-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **risk_register** — `processor` → `processor/risk-register-updater`
16. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/pipeline-integrity-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/oil-gas-pipeline-integrity-frameworks`
- **rule_packs**: `rule-pack/grep-oil-gas-pipeline-integrity-flags`, `rule-pack/rag-oil-gas-pipeline-integrity-retrieval-policy`

## Success criteria

- rubric `rubric/oil-gas-pipeline-integrity-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/oil-gas-pipeline-integrity-review` v0.1.0
- License: `MIT`
- Industry: energy.oil_gas, infrastructure
- Full source manifest: see `references/manifest.yaml`
