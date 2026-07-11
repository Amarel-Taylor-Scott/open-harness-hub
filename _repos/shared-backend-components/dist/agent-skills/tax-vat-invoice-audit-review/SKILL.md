---
name: tax-vat-invoice-audit-review
description: Review VAT/GST invoice packets for registration, tax rate, reverse charge,
  place of supply, and recovery evidence.
when_to_use: 'Pipeline kind: review.'
---

# Tax VAT Invoice Audit review pipeline

Benchmarkable tax vat invoice audit review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review VAT/GST invoice packets for registration, tax rate, reverse charge, place of supply, and recovery evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-tax-vat-invoice-audit-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-tax-vat-invoice-audit-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/tax-vat-invoice-audit-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/vat-invoice-auditor
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/tax-vat-invoice-audit-frameworks`
- **rule_packs**: `rule-pack/grep-tax-vat-invoice-audit-flags`, `rule-pack/rag-tax-vat-invoice-audit-retrieval-policy`

## Success criteria

- rubric `rubric/tax-vat-invoice-audit-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/tax-vat-invoice-audit-review` v0.1.0
- License: `MIT`
- Industry: tax.indirect, finance.fraud
- Full source manifest: see `references/manifest.yaml`
