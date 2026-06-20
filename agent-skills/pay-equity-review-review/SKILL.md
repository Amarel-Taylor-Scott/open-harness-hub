---
name: pay-equity-review-review
description: Review pay-equity packets for cohort definition, legitimate factors,
  outlier remediation, and legal review evidence.
when_to_use: 'Pipeline kind: review.'
---

# Pay Equity Review review pipeline

Benchmarkable pay equity review review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review pay-equity packets for cohort definition, legitimate factors, outlier remediation, and legal review evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-pay-equity-review-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-pay-equity-review-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/pay-equity-review-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/pay-equity-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/pay-equity-review-frameworks`
- **rule_packs**: `rule-pack/grep-pay-equity-review-flags`, `rule-pack/rag-pay-equity-review-retrieval-policy`

## Success criteria

- rubric `rubric/pay-equity-review-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/pay-equity-review-review` v0.1.0
- License: `MIT`
- Industry: hr.compensation, compliance
- Full source manifest: see `references/manifest.yaml`
