---
name: rail-equipment-defect-review
description: Review rail equipment defect packets for safety severity, inspection
  evidence, repair status, and operating restrictions.
when_to_use: 'Pipeline kind: review.'
---

# Rail Equipment Defect review pipeline

Expanded rail equipment defect review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review rail equipment defect packets for safety severity, inspection evidence, repair status, and operating restrictions.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-rail-equipment-defect-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-rail-equipment-defect-retrieval-policy`
6. **review_harness** — `harness` → `harness/rail-equipment-defect-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/rail-equipment-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/rail-equipment-defect-frameworks`
- **rule_packs**: `rule-pack/grep-rail-equipment-defect-flags`, `rule-pack/rag-rail-equipment-defect-retrieval-policy`

## Success criteria

- rubric `rubric/rail-equipment-defect-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/rail-equipment-defect-review` v0.1.0
- License: `MIT`
- Industry: transportation.rail
- Full source manifest: see `references/manifest.yaml`
