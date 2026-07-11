---
name: biosecurity-review
description: Review select-agent registered entity compliance packet.
when_to_use: 'Pipeline kind: review.'
---

# Biosecurity / select agent review (42 CFR 73 + BMBL 6e + DURC/P3CO)

Vertical 32 — registered select-agent entity + BSL-3/4 lab compliance + DURC.

## Task

Review select-agent registered entity compliance packet.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-biosecurity-flags`
4. **rag_against_cdc** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/biosecurity-officer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-biosecurity-flags`
- **knowledge_packs**: `knowledge-pack/biosecurity-frameworks`

## Success criteria

- rubric `rubric/biosecurity-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/biosecurity-review` v0.1.0
- License: `MIT`
- Industry: biosecurity, biosecurity.select_agent, biosecurity.bsl, biosecurity.durc, compliance
- Full source manifest: see `references/manifest.yaml`
