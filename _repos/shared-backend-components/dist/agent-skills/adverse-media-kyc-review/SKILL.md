---
name: adverse-media-kyc-review
description: Review adverse-media packets for entity match, source credibility, allegation
  severity, and onboarding decision.
when_to_use: 'Pipeline kind: review.'
---

# Adverse Media KYC review pipeline

Expanded adverse media kyc review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review adverse-media packets for entity match, source credibility, allegation severity, and onboarding decision.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-adverse-media-kyc-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-adverse-media-kyc-retrieval-policy`
6. **review_harness** — `harness` → `harness/adverse-media-kyc-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/adverse-media-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/adverse-media-kyc-frameworks`
- **rule_packs**: `rule-pack/grep-adverse-media-kyc-flags`, `rule-pack/rag-adverse-media-kyc-retrieval-policy`

## Success criteria

- rubric `rubric/adverse-media-kyc-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/adverse-media-kyc-review` v0.1.0
- License: `MIT`
- Industry: finance.kyc, finance.aml
- Full source manifest: see `references/manifest.yaml`
