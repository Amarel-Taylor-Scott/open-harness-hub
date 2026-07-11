---
name: food-safety-review
description: Review a food-safety facility's HACCP plan + supplier verification +
  traceability.
when_to_use: 'Pipeline kind: review.'
---

# Food safety review (FDA FSMA + HACCP + GFSI)

Seventeenth vertical.

## Task

Review a food-safety facility's HACCP plan + supplier verification + traceability.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-food-safety-flags`
4. **rag_against_frameworks** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/food-safety-officer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-food-safety-flags`
- **knowledge_packs**: `knowledge-pack/food-safety-fsma-haccp`

## Success criteria

- rubric `rubric/food-safety-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/food-safety-review` v0.1.0
- License: `MIT`
- Industry: food_safety, food_safety.fsma, food_safety.haccp
- Full source manifest: see `references/manifest.yaml`
