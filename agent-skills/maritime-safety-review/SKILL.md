---
name: maritime-safety-review
description: Review vessel inspection / PSC / ISM audit packet.
when_to_use: 'Pipeline kind: review.'
---

# Maritime safety review (IMO SOLAS / MARPOL / ISM / STCW)

Vertical 20.

## Task

Review vessel inspection / PSC / ISM audit packet.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-maritime-safety-flags`
4. **rag_against_imo** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/maritime-safety-officer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-maritime-safety-flags`
- **knowledge_packs**: `knowledge-pack/imo-conventions`

## Success criteria

- rubric `rubric/maritime-safety-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/maritime-safety-review` v0.1.0
- License: `MIT`
- Industry: maritime, maritime.safety
- Full source manifest: see `references/manifest.yaml`
