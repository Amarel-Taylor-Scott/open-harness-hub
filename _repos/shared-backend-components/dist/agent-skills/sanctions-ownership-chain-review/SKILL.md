---
name: sanctions-ownership-chain-review
description: Review ownership-chain packets for beneficial ownership, control, sanctions
  proximity, aliases, and screening evidence.
when_to_use: 'Pipeline kind: review.'
---

# Sanctions Ownership Chain review pipeline

Benchmarkable sanctions ownership chain review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review ownership-chain packets for beneficial ownership, control, sanctions proximity, aliases, and screening evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-sanctions-ownership-chain-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-sanctions-ownership-chain-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/sanctions-ownership-chain-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/ownership-chain-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/sanctions-ownership-chain-frameworks`
- **rule_packs**: `rule-pack/grep-sanctions-ownership-chain-flags`, `rule-pack/rag-sanctions-ownership-chain-retrieval-policy`

## Success criteria

- rubric `rubric/sanctions-ownership-chain-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/sanctions-ownership-chain-review` v0.1.0
- License: `MIT`
- Industry: trade.sanctions, finance.kyc
- Full source manifest: see `references/manifest.yaml`
