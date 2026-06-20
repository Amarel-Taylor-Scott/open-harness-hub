---
name: ma-dd-review
description: Review M&A target DD packet across 6 streams + propose disposition.
when_to_use: 'Pipeline kind: review.'
---

# M&A due-diligence review (6-stream)

Fifteenth vertical.

## Task

Review M&A target DD packet across 6 streams + propose disposition.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-ma-dd-red-flags`
4. **rag_against_frameworks** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/ma-dd-counsel
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-ma-dd-red-flags`
- **knowledge_packs**: `knowledge-pack/ma-dd-frameworks`

## Success criteria

- rubric `rubric/ma-dd-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/ma-dd-review` v0.1.0
- License: `MIT`
- Industry: m_and_a, m_and_a.due_diligence, legal, finance
- Full source manifest: see `references/manifest.yaml`
