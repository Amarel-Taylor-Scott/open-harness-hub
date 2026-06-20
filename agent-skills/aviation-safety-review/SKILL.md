---
name: aviation-safety-review
description: Classify causation per HFACS + cite NTSB taxonomy + propose corrective
  actions.
when_to_use: 'Pipeline kind: review.'
---

# Aviation safety incident review

Sixteenth vertical.

## Task

Classify causation per HFACS + cite NTSB taxonomy + propose corrective actions.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-aviation-safety-flags`
4. **rag_against_frameworks** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/aviation-safety-investigator
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-aviation-safety-flags`
- **knowledge_packs**: `knowledge-pack/aviation-safety-frameworks`

## Success criteria

- rubric `rubric/aviation-safety-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/aviation-safety-review` v0.1.0
- License: `MIT`
- Industry: aviation, aviation.safety
- Full source manifest: see `references/manifest.yaml`
