---
name: drinking-water-sampling-plan-review
description: Review drinking-water sampling plans for site selection, frequency, chain
  of custody, exceedance response, and public notice.
when_to_use: 'Pipeline kind: review.'
---

# Drinking Water Sampling Plan review pipeline

Benchmarkable drinking water sampling plan review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review drinking-water sampling plans for site selection, frequency, chain of custody, exceedance response, and public notice.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-drinking-water-sampling-plan-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-drinking-water-sampling-plan-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/drinking-water-sampling-plan-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/water-sampling-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/drinking-water-sampling-plan-frameworks`
- **rule_packs**: `rule-pack/grep-drinking-water-sampling-plan-flags`, `rule-pack/rag-drinking-water-sampling-plan-retrieval-policy`

## Success criteria

- rubric `rubric/drinking-water-sampling-plan-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/drinking-water-sampling-plan-review` v0.1.0
- License: `MIT`
- Industry: environmental.water, water_utility.sdwa
- Full source manifest: see `references/manifest.yaml`
