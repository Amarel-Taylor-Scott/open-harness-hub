---
name: customs-origin-fta-review
description: Review free-trade agreement origin packets for qualification, supplier
  declarations, tariff shift, and recordkeeping evidence.
when_to_use: 'Pipeline kind: review.'
---

# Customs Origin FTA review pipeline

Benchmarkable customs origin fta review pipeline with normalization, grep, RAG, harness review, severity calibration, evidence gaps, and risk-register output.

## Task

Review free-trade agreement origin packets for qualification, supplier declarations, tariff shift, and recordkeeping evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-customs-origin-fta-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-customs-origin-fta-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/customs-origin-fta-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **risk_register** — `processor` → `processor/risk-register-updater`
16. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/fta-origin-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/customs-origin-fta-frameworks`
- **rule_packs**: `rule-pack/grep-customs-origin-fta-flags`, `rule-pack/rag-customs-origin-fta-retrieval-policy`

## Success criteria

- rubric `rubric/customs-origin-fta-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/customs-origin-fta-review` v0.1.0
- License: `MIT`
- Industry: customs.fta, trade.hts
- Full source manifest: see `references/manifest.yaml`
