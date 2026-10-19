---
name: treasury-wire-approval-review
description: Review treasury wire packets for beneficiary validation, approval authority,
  sanctions, fraud indicators, and callback evidence.
when_to_use: 'Pipeline kind: review.'
---

# Treasury Wire Approval review pipeline

Benchmarkable treasury wire approval review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review treasury wire packets for beneficiary validation, approval authority, sanctions, fraud indicators, and callback evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-treasury-wire-approval-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-treasury-wire-approval-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/treasury-wire-approval-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/treasury-wire-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/treasury-wire-approval-frameworks`
- **rule_packs**: `rule-pack/grep-treasury-wire-approval-flags`, `rule-pack/rag-treasury-wire-approval-retrieval-policy`

## Success criteria

- rubric `rubric/treasury-wire-approval-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/treasury-wire-approval-review` v0.1.0
- License: `MIT`
- Industry: finance.fraud, finance.kyc
- Full source manifest: see `references/manifest.yaml`
