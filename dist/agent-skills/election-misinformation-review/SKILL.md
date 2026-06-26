---
name: election-misinformation-review
description: Review election-related content for mis/dis/mal-information + synthetic-media
  indicators + voter-suppression vectors.
when_to_use: 'Pipeline kind: review.'
---

# Election misinformation / disinformation / synthetic-media review

Vertical 23 — election integrity. Same 6-step chain.

## Task

Review election-related content for mis/dis/mal-information + synthetic-media indicators + voter-suppression vectors.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-election-misinformation-flags`
4. **rag_against_frameworks** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/election-integrity-analyst
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-election-misinformation-flags`
- **knowledge_packs**: `knowledge-pack/election-integrity-frameworks`

## Success criteria

- rubric `rubric/election-integrity-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/election-misinformation-review` v0.1.0
- License: `MIT`
- Industry: election_integrity, media, media.factcheck
- Full source manifest: see `references/manifest.yaml`
