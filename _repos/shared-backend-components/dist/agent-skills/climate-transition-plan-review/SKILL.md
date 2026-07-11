---
name: climate-transition-plan-review
description: Review climate transition plans for targets, capex alignment, offsets,
  scope coverage, governance, and credibility gaps.
when_to_use: 'Pipeline kind: review.'
---

# Climate Transition Plan review pipeline

Benchmarkable climate transition plan review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review climate transition plans for targets, capex alignment, offsets, scope coverage, governance, and credibility gaps.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-climate-transition-plan-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-climate-transition-plan-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/climate-transition-plan-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/transition-plan-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/climate-transition-plan-frameworks`
- **rule_packs**: `rule-pack/grep-climate-transition-plan-flags`, `rule-pack/rag-climate-transition-plan-retrieval-policy`

## Success criteria

- rubric `rubric/climate-transition-plan-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/climate-transition-plan-review` v0.1.0
- License: `MIT`
- Industry: climate, esg.csrd
- Full source manifest: see `references/manifest.yaml`
