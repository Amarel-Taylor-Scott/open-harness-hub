---
name: cookie-consent-audit-review
description: Review cookie consent implementations for prior consent, categories,
  reject parity, records, and tag behavior.
when_to_use: 'Pipeline kind: review.'
---

# Cookie Consent Audit review pipeline

Benchmarkable cookie consent audit review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review cookie consent implementations for prior consent, categories, reject parity, records, and tag behavior.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-cookie-consent-audit-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-cookie-consent-audit-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/cookie-consent-audit-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/cookie-consent-auditor
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/cookie-consent-audit-frameworks`
- **rule_packs**: `rule-pack/grep-cookie-consent-audit-flags`, `rule-pack/rag-cookie-consent-audit-retrieval-policy`

## Success criteria

- rubric `rubric/cookie-consent-audit-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/cookie-consent-audit-review` v0.1.0
- License: `MIT`
- Industry: privacy.gdpr, marketing_ops.consent
- Full source manifest: see `references/manifest.yaml`
