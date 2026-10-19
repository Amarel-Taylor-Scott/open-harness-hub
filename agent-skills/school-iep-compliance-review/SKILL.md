---
name: school-iep-compliance-review
description: Review IEP packets for timelines, services, accommodations, consent,
  and implementation evidence.
when_to_use: 'Pipeline kind: review.'
---

# School IEP Compliance review pipeline

Expanded school iep compliance review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review IEP packets for timelines, services, accommodations, consent, and implementation evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-school-iep-compliance-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-school-iep-compliance-retrieval-policy`
6. **review_harness** — `harness` → `harness/school-iep-compliance-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/iep-compliance-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/school-iep-compliance-frameworks`
- **rule_packs**: `rule-pack/grep-school-iep-compliance-flags`, `rule-pack/rag-school-iep-compliance-retrieval-policy`

## Success criteria

- rubric `rubric/school-iep-compliance-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/school-iep-compliance-review` v0.1.0
- License: `MIT`
- Industry: education.k12
- Full source manifest: see `references/manifest.yaml`
