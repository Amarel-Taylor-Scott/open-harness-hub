---
name: charity-donor-restriction-review
description: Review donor-restricted fund packets for purpose restrictions, release
  conditions, reporting, and spend evidence.
when_to_use: 'Pipeline kind: review.'
---

# Charity Donor Restriction review pipeline

Expanded charity donor restriction review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review donor-restricted fund packets for purpose restrictions, release conditions, reporting, and spend evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-charity-donor-restriction-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-charity-donor-restriction-retrieval-policy`
6. **review_harness** — `harness` → `harness/charity-donor-restriction-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/donor-restriction-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/charity-donor-restriction-frameworks`
- **rule_packs**: `rule-pack/grep-charity-donor-restriction-flags`, `rule-pack/rag-charity-donor-restriction-retrieval-policy`

## Success criteria

- rubric `rubric/charity-donor-restriction-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/charity-donor-restriction-review` v0.1.0
- License: `MIT`
- Industry: nonprofit
- Full source manifest: see `references/manifest.yaml`
