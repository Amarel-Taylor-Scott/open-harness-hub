---
name: forestry-harvest-compliance-review
description: Review forestry harvest packets for permits, buffer protection, erosion
  controls, road impacts, and replanting obligations.
when_to_use: 'Pipeline kind: review.'
---

# Forestry Harvest Compliance review pipeline

Benchmarkable forestry harvest compliance review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review forestry harvest packets for permits, buffer protection, erosion controls, road impacts, and replanting obligations.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-forestry-harvest-compliance-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-forestry-harvest-compliance-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/forestry-harvest-compliance-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/forestry-harvest-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/forestry-harvest-compliance-frameworks`
- **rule_packs**: `rule-pack/grep-forestry-harvest-compliance-flags`, `rule-pack/rag-forestry-harvest-compliance-retrieval-policy`

## Success criteria

- rubric `rubric/forestry-harvest-compliance-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/forestry-harvest-compliance-review` v0.1.0
- License: `MIT`
- Industry: environmental.water, sustainability
- Full source manifest: see `references/manifest.yaml`
