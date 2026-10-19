---
name: travel-disruption-care-review
description: Review travel disruption cases for duty-of-care response, rebooking,
  compensation, and customer communication.
when_to_use: 'Pipeline kind: review.'
---

# Travel Disruption Care review pipeline

Expanded travel disruption care review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review travel disruption cases for duty-of-care response, rebooking, compensation, and customer communication.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-travel-disruption-care-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-travel-disruption-care-retrieval-policy`
6. **review_harness** — `harness` → `harness/travel-disruption-care-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/travel-disruption-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/travel-disruption-care-frameworks`
- **rule_packs**: `rule-pack/grep-travel-disruption-care-flags`, `rule-pack/rag-travel-disruption-care-retrieval-policy`

## Success criteria

- rubric `rubric/travel-disruption-care-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/travel-disruption-care-review` v0.1.0
- License: `MIT`
- Industry: hospitality, transportation
- Full source manifest: see `references/manifest.yaml`
