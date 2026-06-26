---
name: water-main-break-response-review
description: Review water main break packets for isolation, pressure loss, boil advisory,
  sampling, repair, and customer communication.
when_to_use: 'Pipeline kind: review.'
---

# Water Main Break Response review pipeline

Benchmarkable water main break response review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review water main break packets for isolation, pressure loss, boil advisory, sampling, repair, and customer communication.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-water-main-break-response-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-water-main-break-response-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/water-main-break-response-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/water-main-response-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/water-main-break-response-frameworks`
- **rule_packs**: `rule-pack/grep-water-main-break-response-flags`, `rule-pack/rag-water-main-break-response-retrieval-policy`

## Success criteria

- rubric `rubric/water-main-break-response-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/water-main-break-response-review` v0.1.0
- License: `MIT`
- Industry: water_utility.sdwa, environmental.water
- Full source manifest: see `references/manifest.yaml`
