---
name: vendor-onboarding-risk-review
description: Review vendor onboarding packets for sanctions, security, privacy, financial,
  insurance, and concentration risk.
when_to_use: 'Pipeline kind: review.'
---

# Vendor Onboarding Risk review pipeline

End-to-end vendor onboarding risk review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review vendor onboarding packets for sanctions, security, privacy, financial, insurance, and concentration risk.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-vendor-onboarding-risk-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-vendor-onboarding-risk-retrieval-policy`
5. **review_harness** — `harness` → `harness/vendor-onboarding-risk-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/vendor-risk-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/vendor-onboarding-risk-frameworks`
- **rule_packs**: `rule-pack/grep-vendor-onboarding-risk-flags`, `rule-pack/rag-vendor-onboarding-risk-retrieval-policy`

## Success criteria

- rubric `rubric/vendor-onboarding-risk-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/vendor-onboarding-risk-review` v0.1.0
- License: `MIT`
- Industry: procurement.vendor_risk, compliance
- Full source manifest: see `references/manifest.yaml`
