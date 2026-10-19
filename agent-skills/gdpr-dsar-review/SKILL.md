---
name: gdpr-dsar-review
description: Review a DSAR fulfillment for completeness + GDPR/CCPA compliance.
when_to_use: 'Pipeline kind: review.'
---

# GDPR DSAR fulfillment review (CCPA-compatible)

Eleventh vertical.

## Task

Review a DSAR fulfillment for completeness + GDPR/CCPA compliance.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-gdpr-dsar-red-flags`
4. **rag_against_gdpr** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/privacy-officer-gdpr
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-gdpr-dsar-red-flags`
- **knowledge_packs**: `knowledge-pack/gdpr-articles-and-ccpa`

## Success criteria

- rubric `rubric/gdpr-dsar-quality-v1` threshold 0.7

## Provenance

- Hub component: `pipeline/gdpr-dsar-review` v0.1.0
- License: `MIT`
- Industry: privacy, privacy.gdpr, privacy.dsar, compliance
- Full source manifest: see `references/manifest.yaml`
