---
name: real-estate-dd-review
description: Review property DD packet.
when_to_use: 'Pipeline kind: review.'
---

# Real estate due-diligence review

Fourteenth vertical.

## Task

Review property DD packet.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-real-estate-dd-red-flags`
4. **rag_against_standards** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/real-estate-dd-analyst
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-real-estate-dd-red-flags`
- **knowledge_packs**: `knowledge-pack/real-estate-dd-standards`

## Success criteria

- rubric `rubric/real-estate-dd-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/real-estate-dd-review` v0.1.0
- License: `MIT`
- Industry: real_estate, real_estate.due_diligence
- Full source manifest: see `references/manifest.yaml`
