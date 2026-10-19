---
name: nuclear-work-order-risk-review
description: Review nuclear maintenance work orders for safety significance, clearance,
  procedure adherence, parts, and post-maintenance testing.
when_to_use: 'Pipeline kind: review.'
---

# Nuclear Work Order Risk review pipeline

Benchmarkable nuclear work order risk review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review nuclear maintenance work orders for safety significance, clearance, procedure adherence, parts, and post-maintenance testing.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-nuclear-work-order-risk-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-nuclear-work-order-risk-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/nuclear-work-order-risk-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/nuclear-work-order-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/nuclear-work-order-risk-frameworks`
- **rule_packs**: `rule-pack/grep-nuclear-work-order-risk-flags`, `rule-pack/rag-nuclear-work-order-risk-retrieval-policy`

## Success criteria

- rubric `rubric/nuclear-work-order-risk-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/nuclear-work-order-risk-review` v0.1.0
- License: `MIT`
- Industry: nuclear.power, energy.grid
- Full source manifest: see `references/manifest.yaml`
