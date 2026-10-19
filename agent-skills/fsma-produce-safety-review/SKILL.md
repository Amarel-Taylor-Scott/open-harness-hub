---
name: fsma-produce-safety-review
description: Review produce safety packets for water testing, worker hygiene, soil
  amendments, wildlife intrusion, and corrective actions.
when_to_use: 'Pipeline kind: review.'
---

# FSMA Produce Safety review pipeline

Benchmarkable fsma produce safety review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review produce safety packets for water testing, worker hygiene, soil amendments, wildlife intrusion, and corrective actions.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-fsma-produce-safety-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-fsma-produce-safety-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/fsma-produce-safety-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/produce-safety-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/fsma-produce-safety-frameworks`
- **rule_packs**: `rule-pack/grep-fsma-produce-safety-flags`, `rule-pack/rag-fsma-produce-safety-retrieval-policy`

## Success criteria

- rubric `rubric/fsma-produce-safety-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/fsma-produce-safety-review` v0.1.0
- License: `MIT`
- Industry: agriculture_compliance.fsma, food.safety
- Full source manifest: see `references/manifest.yaml`
