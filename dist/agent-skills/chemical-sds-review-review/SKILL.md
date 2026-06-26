---
name: chemical-sds-review-review
description: Review chemical safety packets for SDS currency, labeling, exposure controls,
  storage compatibility, and training gaps.
when_to_use: 'Pipeline kind: review.'
---

# Chemical SDS Review review pipeline

Benchmarkable chemical sds review review pipeline with normalization, grep, RAG, harness review, severity calibration, evidence gaps, and risk-register output.

## Task

Review chemical safety packets for SDS currency, labeling, exposure controls, storage compatibility, and training gaps.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-chemical-sds-review-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-chemical-sds-review-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/chemical-sds-review-review`
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

- **persona**: persona/chemical-sds-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/chemical-sds-review-frameworks`
- **rule_packs**: `rule-pack/grep-chemical-sds-review-flags`, `rule-pack/rag-chemical-sds-review-retrieval-policy`

## Success criteria

- rubric `rubric/chemical-sds-review-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/chemical-sds-review-review` v0.1.0
- License: `MIT`
- Industry: ehs.audit, manufacturing.qa
- Full source manifest: see `references/manifest.yaml`
