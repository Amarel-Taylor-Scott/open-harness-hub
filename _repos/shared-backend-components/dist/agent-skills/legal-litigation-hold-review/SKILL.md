---
name: legal-litigation-hold-review
description: Review litigation hold packets for custodian scope, preservation notices,
  collection status, and release controls.
when_to_use: 'Pipeline kind: review.'
---

# Legal Litigation Hold review pipeline

Expanded legal litigation hold review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review litigation hold packets for custodian scope, preservation notices, collection status, and release controls.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-legal-litigation-hold-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-legal-litigation-hold-retrieval-policy`
6. **review_harness** — `harness` → `harness/legal-litigation-hold-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/litigation-hold-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/legal-litigation-hold-frameworks`
- **rule_packs**: `rule-pack/grep-legal-litigation-hold-flags`, `rule-pack/rag-legal-litigation-hold-retrieval-policy`

## Success criteria

- rubric `rubric/legal-litigation-hold-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/legal-litigation-hold-review` v0.1.0
- License: `MIT`
- Industry: legal.litigation
- Full source manifest: see `references/manifest.yaml`
