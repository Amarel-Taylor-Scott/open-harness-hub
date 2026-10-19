---
name: cloud-cost-anomaly-review
description: Review cloud cost anomalies for source, owner, budget impact, waste,
  and remediation.
when_to_use: 'Pipeline kind: review.'
---

# Cloud Cost Anomaly review pipeline

Expanded cloud cost anomaly review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review cloud cost anomalies for source, owner, budget impact, waste, and remediation.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-cloud-cost-anomaly-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-cloud-cost-anomaly-retrieval-policy`
6. **review_harness** — `harness` → `harness/cloud-cost-anomaly-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/cloud-cost-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/cloud-cost-anomaly-frameworks`
- **rule_packs**: `rule-pack/grep-cloud-cost-anomaly-flags`, `rule-pack/rag-cloud-cost-anomaly-retrieval-policy`

## Success criteria

- rubric `rubric/cloud-cost-anomaly-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/cloud-cost-anomaly-review` v0.1.0
- License: `MIT`
- Industry: software.devops, sre
- Full source manifest: see `references/manifest.yaml`
