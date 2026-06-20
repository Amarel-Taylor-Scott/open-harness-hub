---
name: cannabis-compliance-review
description: Review cannabis operator compliance packet.
when_to_use: 'Pipeline kind: review.'
---

# Cannabis compliance review (state + §280E + METRC + FinCEN)

Vertical 31 — licensed cannabis operator compliance.

## Task

Review cannabis operator compliance packet.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-cannabis-compliance-flags`
4. **rag_against_state** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/cannabis-compliance-officer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-cannabis-compliance-flags`
- **knowledge_packs**: `knowledge-pack/cannabis-frameworks`

## Success criteria

- rubric `rubric/cannabis-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/cannabis-compliance-review` v0.1.0
- License: `MIT`
- Industry: cannabis, cannabis.cultivation, cannabis.retail, cannabis.testing, compliance
- Full source manifest: see `references/manifest.yaml`
