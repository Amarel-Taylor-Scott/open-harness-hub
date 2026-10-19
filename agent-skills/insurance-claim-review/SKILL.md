---
name: insurance-claim-review
description: Grade an insurance claim submission against the rubric + surface fraud
  indicators.
when_to_use: 'Pipeline kind: review.'
---

# Insurance claim review (NAIC fraud-aware)

Eighth vertical proving the architecture's industry-agnosticism.
Same 6-step chain — only persona/rule-pack/knowledge-pack/rubric
change.

## Task

Grade an insurance claim submission against the rubric + surface fraud indicators.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_indicators** — `rule_pack` → `rule-pack/grep-insurance-fraud-red-flags`
4. **rag_against_typologies** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/insurance-claims-adjuster
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-insurance-fraud-red-flags`
- **knowledge_packs**: `knowledge-pack/insurance-fraud-typologies`

## Success criteria

- rubric `rubric/insurance-claim-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/insurance-claim-review` v0.1.0
- License: `MIT`
- Industry: insurance, insurance.claims, insurance.fraud, finance
- Full source manifest: see `references/manifest.yaml`
