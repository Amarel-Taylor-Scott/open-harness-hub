---
name: construction-safety-review
description: Review a construction-site safety packet (JHA + toolbox talks + inspection
  notes + near-misses).
when_to_use: 'Pipeline kind: review.'
---

# Construction safety review (OSHA 1926 / Focus Four)

Vertical 18.

## Task

Review a construction-site safety packet (JHA + toolbox talks + inspection notes + near-misses).

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-construction-safety-flags`
4. **rag_against_osha** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/construction-safety-officer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-construction-safety-flags`
- **knowledge_packs**: `knowledge-pack/osha-construction-1926`

## Success criteria

- rubric `rubric/construction-safety-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/construction-safety-review` v0.1.0
- License: `MIT`
- Industry: construction, construction.safety
- Full source manifest: see `references/manifest.yaml`
