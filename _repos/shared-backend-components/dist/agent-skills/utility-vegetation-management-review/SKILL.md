---
name: utility-vegetation-management-review
description: Review utility vegetation packets for hazard trees, circuit risk, environmental
  constraints, customer notices, and completion evidence.
when_to_use: 'Pipeline kind: review.'
---

# Utility Vegetation Management review pipeline

Benchmarkable utility vegetation management review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review utility vegetation packets for hazard trees, circuit risk, environmental constraints, customer notices, and completion evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-utility-vegetation-management-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-utility-vegetation-management-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/utility-vegetation-management-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/vegetation-management-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/utility-vegetation-management-frameworks`
- **rule_packs**: `rule-pack/grep-utility-vegetation-management-flags`, `rule-pack/rag-utility-vegetation-management-retrieval-policy`

## Success criteria

- rubric `rubric/utility-vegetation-management-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/utility-vegetation-management-review` v0.1.0
- License: `MIT`
- Industry: energy.grid, environmental.water
- Full source manifest: see `references/manifest.yaml`
