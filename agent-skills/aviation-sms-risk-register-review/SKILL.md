---
name: aviation-sms-risk-register-review
description: Review aviation SMS risk register packets for hazard identification,
  risk controls, accountable owners, and monitoring.
when_to_use: 'Pipeline kind: review.'
---

# Aviation SMS Risk Register review pipeline

Benchmarkable aviation sms risk register review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review aviation SMS risk register packets for hazard identification, risk controls, accountable owners, and monitoring.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-aviation-sms-risk-register-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-aviation-sms-risk-register-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/aviation-sms-risk-register-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/sms-risk-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/aviation-sms-risk-register-frameworks`
- **rule_packs**: `rule-pack/grep-aviation-sms-risk-register-flags`, `rule-pack/rag-aviation-sms-risk-register-retrieval-policy`

## Success criteria

- rubric `rubric/aviation-sms-risk-register-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/aviation-sms-risk-register-review` v0.1.0
- License: `MIT`
- Industry: aviation.safety, aviation.maintenance
- Full source manifest: see `references/manifest.yaml`
