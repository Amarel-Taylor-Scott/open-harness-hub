---
name: building-code-inspection-review
description: Review building inspection packets for code deficiencies, life-safety
  issues, correction notices, and reinspection status.
when_to_use: 'Pipeline kind: review.'
---

# Building Code Inspection review pipeline

Expanded building code inspection review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review building inspection packets for code deficiencies, life-safety issues, correction notices, and reinspection status.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-building-code-inspection-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-building-code-inspection-retrieval-policy`
6. **review_harness** — `harness` → `harness/building-code-inspection-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/building-code-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/building-code-inspection-frameworks`
- **rule_packs**: `rule-pack/grep-building-code-inspection-flags`, `rule-pack/rag-building-code-inspection-retrieval-policy`

## Success criteria

- rubric `rubric/building-code-inspection-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/building-code-inspection-review` v0.1.0
- License: `MIT`
- Industry: construction.permitting, infrastructure
- Full source manifest: see `references/manifest.yaml`
