---
name: food-recall-effectiveness-review
description: Review food recall packets for consignee notification, product reconciliation,
  public notice, root cause, and effectiveness checks.
when_to_use: 'Pipeline kind: review.'
---

# Food Recall Effectiveness review pipeline

Benchmarkable food recall effectiveness review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review food recall packets for consignee notification, product reconciliation, public notice, root cause, and effectiveness checks.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-food-recall-effectiveness-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-food-recall-effectiveness-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/food-recall-effectiveness-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/recall-effectiveness-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/food-recall-effectiveness-frameworks`
- **rule_packs**: `rule-pack/grep-food-recall-effectiveness-flags`, `rule-pack/rag-food-recall-effectiveness-retrieval-policy`

## Success criteria

- rubric `rubric/food-recall-effectiveness-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/food-recall-effectiveness-review` v0.1.0
- License: `MIT`
- Industry: food_safety.recall, food.safety
- Full source manifest: see `references/manifest.yaml`
