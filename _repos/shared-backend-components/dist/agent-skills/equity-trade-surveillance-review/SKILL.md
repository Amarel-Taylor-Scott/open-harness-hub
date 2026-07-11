---
name: equity-trade-surveillance-review
description: Review trade surveillance packets for manipulation, wash trades, spoofing,
  best execution, and escalation evidence.
when_to_use: 'Pipeline kind: review.'
---

# Equity Trade Surveillance review pipeline

Benchmarkable equity trade surveillance review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review trade surveillance packets for manipulation, wash trades, spoofing, best execution, and escalation evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-equity-trade-surveillance-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-equity-trade-surveillance-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/equity-trade-surveillance-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/equity-surveillance-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/equity-trade-surveillance-frameworks`
- **rule_packs**: `rule-pack/grep-equity-trade-surveillance-flags`, `rule-pack/rag-equity-trade-surveillance-retrieval-policy`

## Success criteria

- rubric `rubric/equity-trade-surveillance-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/equity-trade-surveillance-review` v0.1.0
- License: `MIT`
- Industry: finance.trading, compliance
- Full source manifest: see `references/manifest.yaml`
