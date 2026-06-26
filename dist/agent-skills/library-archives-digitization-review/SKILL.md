---
name: library-archives-digitization-review
description: Review archival digitization packets for rights, metadata, preservation,
  redaction, and accessibility readiness.
when_to_use: 'Pipeline kind: review.'
---

# Library Archives Digitization review pipeline

Benchmarkable library archives digitization review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review archival digitization packets for rights, metadata, preservation, redaction, and accessibility readiness.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-library-archives-digitization-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-library-archives-digitization-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/library-archives-digitization-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/archives-digitization-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/library-archives-digitization-frameworks`
- **rule_packs**: `rule-pack/grep-library-archives-digitization-flags`, `rule-pack/rag-library-archives-digitization-retrieval-policy`

## Success criteria

- rubric `rubric/library-archives-digitization-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/library-archives-digitization-review` v0.1.0
- License: `MIT`
- Industry: education.higher, media.editorial
- Full source manifest: see `references/manifest.yaml`
