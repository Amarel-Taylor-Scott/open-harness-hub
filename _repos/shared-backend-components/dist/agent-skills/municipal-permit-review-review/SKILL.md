---
name: municipal-permit-review-review
description: Review permit applications for completeness, zoning/code evidence, public
  notice, and approval conditions.
when_to_use: 'Pipeline kind: review.'
---

# Municipal Permit Review review pipeline

Expanded municipal permit review review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review permit applications for completeness, zoning/code evidence, public notice, and approval conditions.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-municipal-permit-review-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-municipal-permit-review-retrieval-policy`
6. **review_harness** — `harness` → `harness/municipal-permit-review-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/permit-review-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/municipal-permit-review-frameworks`
- **rule_packs**: `rule-pack/grep-municipal-permit-review-flags`, `rule-pack/rag-municipal-permit-review-retrieval-policy`

## Success criteria

- rubric `rubric/municipal-permit-review-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/municipal-permit-review-review` v0.1.0
- License: `MIT`
- Industry: government.permitting
- Full source manifest: see `references/manifest.yaml`
