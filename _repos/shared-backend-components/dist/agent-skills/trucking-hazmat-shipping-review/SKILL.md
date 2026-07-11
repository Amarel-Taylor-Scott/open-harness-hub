---
name: trucking-hazmat-shipping-review
description: Review hazmat shipping packets for classification, placards, shipping
  papers, training, routing, and incident readiness.
when_to_use: 'Pipeline kind: review.'
---

# Trucking Hazmat Shipping review pipeline

Benchmarkable trucking hazmat shipping review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review hazmat shipping packets for classification, placards, shipping papers, training, routing, and incident readiness.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-trucking-hazmat-shipping-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-trucking-hazmat-shipping-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/trucking-hazmat-shipping-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/hazmat-shipping-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/trucking-hazmat-shipping-frameworks`
- **rule_packs**: `rule-pack/grep-trucking-hazmat-shipping-flags`, `rule-pack/rag-trucking-hazmat-shipping-retrieval-policy`

## Success criteria

- rubric `rubric/trucking-hazmat-shipping-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/trucking-hazmat-shipping-review` v0.1.0
- License: `MIT`
- Industry: transportation.trucking, trade
- Full source manifest: see `references/manifest.yaml`
