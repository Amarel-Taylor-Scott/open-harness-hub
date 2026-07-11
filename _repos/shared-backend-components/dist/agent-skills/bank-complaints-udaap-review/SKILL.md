---
name: bank-complaints-udaap-review
description: Review banking complaints for UDAAP risk, remediation, root cause, and
  regulatory response readiness.
when_to_use: 'Pipeline kind: review.'
---

# Bank Complaints UDAAP review pipeline

Expanded bank complaints udaap review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review banking complaints for UDAAP risk, remediation, root cause, and regulatory response readiness.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-bank-complaints-udaap-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-bank-complaints-udaap-retrieval-policy`
6. **review_harness** — `harness` → `harness/bank-complaints-udaap-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/bank-complaint-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/bank-complaints-udaap-frameworks`
- **rule_packs**: `rule-pack/grep-bank-complaints-udaap-flags`, `rule-pack/rag-bank-complaints-udaap-retrieval-policy`

## Success criteria

- rubric `rubric/bank-complaints-udaap-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/bank-complaints-udaap-review` v0.1.0
- License: `MIT`
- Industry: finance, compliance
- Full source manifest: see `references/manifest.yaml`
