---
name: rag-citation-audit-review
description: Review RAG answers for citation coverage, unsupported claims, stale context,
  and retrieval quality.
when_to_use: 'Pipeline kind: review.'
---

# RAG Citation Audit review pipeline

Expanded rag citation audit review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review RAG answers for citation coverage, unsupported claims, stale context, and retrieval quality.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-rag-citation-audit-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-rag-citation-audit-retrieval-policy`
6. **review_harness** — `harness` → `harness/rag-citation-audit-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/rag-citation-auditor
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/rag-citation-audit-frameworks`
- **rule_packs**: `rule-pack/grep-rag-citation-audit-flags`, `rule-pack/rag-rag-citation-audit-retrieval-policy`

## Success criteria

- rubric `rubric/rag-citation-audit-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/rag-citation-audit-review` v0.1.0
- License: `MIT`
- Industry: ai, cross_industry
- Full source manifest: see `references/manifest.yaml`
