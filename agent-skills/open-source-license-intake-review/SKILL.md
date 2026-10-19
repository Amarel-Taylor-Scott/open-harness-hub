---
name: open-source-license-intake-review
description: Review dependency intake packets for license compatibility, attribution,
  copyleft, and security metadata.
when_to_use: 'Pipeline kind: review.'
---

# Open Source License Intake review pipeline

Expanded open source license intake review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review dependency intake packets for license compatibility, attribution, copyleft, and security metadata.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-open-source-license-intake-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-open-source-license-intake-retrieval-policy`
6. **review_harness** — `harness` → `harness/open-source-license-intake-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/oss-license-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/open-source-license-intake-frameworks`
- **rule_packs**: `rule-pack/grep-open-source-license-intake-flags`, `rule-pack/rag-open-source-license-intake-retrieval-policy`

## Success criteria

- rubric `rubric/open-source-license-intake-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/open-source-license-intake-review` v0.1.0
- License: `MIT`
- Industry: software, legal.ip
- Full source manifest: see `references/manifest.yaml`
