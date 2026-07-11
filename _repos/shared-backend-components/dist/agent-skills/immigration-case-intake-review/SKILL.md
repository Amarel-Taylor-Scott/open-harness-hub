---
name: immigration-case-intake-review
description: Review immigration intake packets for eligibility evidence, deadline
  risk, translation, and missing documents.
when_to_use: 'Pipeline kind: review.'
---

# Immigration Case Intake review pipeline

Expanded immigration case intake review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review immigration intake packets for eligibility evidence, deadline risk, translation, and missing documents.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-immigration-case-intake-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-immigration-case-intake-retrieval-policy`
6. **review_harness** — `harness` → `harness/immigration-case-intake-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/immigration-intake-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/immigration-case-intake-frameworks`
- **rule_packs**: `rule-pack/grep-immigration-case-intake-flags`, `rule-pack/rag-immigration-case-intake-retrieval-policy`

## Success criteria

- rubric `rubric/immigration-case-intake-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/immigration-case-intake-review` v0.1.0
- License: `MIT`
- Industry: legal.immigration
- Full source manifest: see `references/manifest.yaml`
