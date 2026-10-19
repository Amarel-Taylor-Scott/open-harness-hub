---
name: trade-compliance-review
description: Review an export transaction for HTS / ECCN / ITAR classification + destination
  + end-user + end-use compliance.
when_to_use: 'Pipeline kind: review.'
---

# Trade compliance review (HTS / EAR / ITAR / OFAC)

Thirteenth vertical.

## Task

Review an export transaction for HTS / ECCN / ITAR classification + destination + end-user + end-use compliance.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-trade-compliance-flags`
4. **rag_against_frameworks** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/trade-compliance-officer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-trade-compliance-flags`
- **knowledge_packs**: `knowledge-pack/trade-export-control-frameworks`

## Success criteria

- rubric `rubric/trade-compliance-quality-v1` threshold 0.7

## Provenance

- Hub component: `pipeline/trade-compliance-review` v0.1.0
- License: `MIT`
- Industry: trade, trade.eccn, trade.itar, trade.sanctions, compliance
- Full source manifest: see `references/manifest.yaml`
