---
name: vector-index-quality-review
description: Review vector index packets for chunking, embedding version, freshness,
  duplicate content, and retrieval regression.
when_to_use: 'Pipeline kind: review.'
---

# Vector Index Quality review pipeline

Benchmarkable vector index quality review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review vector index packets for chunking, embedding version, freshness, duplicate content, and retrieval regression.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-vector-index-quality-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-vector-index-quality-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/vector-index-quality-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/vector-index-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/vector-index-quality-frameworks`
- **rule_packs**: `rule-pack/grep-vector-index-quality-flags`, `rule-pack/rag-vector-index-quality-retrieval-policy`

## Success criteria

- rubric `rubric/vector-index-quality-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/vector-index-quality-review` v0.1.0
- License: `MIT`
- Industry: ai, data_governance.quality
- Full source manifest: see `references/manifest.yaml`
