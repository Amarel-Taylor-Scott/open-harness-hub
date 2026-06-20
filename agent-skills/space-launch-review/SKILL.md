---
name: space-launch-review
description: Review commercial space launch readiness packet.
when_to_use: 'Pipeline kind: review.'
---

# Space launch + range safety review (FAA Part 450 / NASA / ITAR)

Vertical 30 — commercial space launch compliance: FSA / Ec / FTS / ITAR / 25-yr disposal / MPL.

## Task

Review commercial space launch readiness packet.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-space-launch-flags`
4. **rag_against_faa** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/space-launch-safety-officer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-space-launch-flags`
- **knowledge_packs**: `knowledge-pack/space-launch-frameworks`

## Success criteria

- rubric `rubric/space-launch-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/space-launch-review` v0.1.0
- License: `MIT`
- Industry: space, space.launch, space.export_control, space.orbital, compliance
- Full source manifest: see `references/manifest.yaml`
