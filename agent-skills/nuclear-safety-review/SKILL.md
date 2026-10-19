---
name: nuclear-safety-review
description: Review nuclear plant compliance packet (LCO + LER + scram analysis +
  physical security + SNM inventory).
when_to_use: 'Pipeline kind: review.'
---

# Nuclear safety review (NRC 10 CFR + IAEA + INPO)

Vertical 27 — nuclear-plant compliance: LCO/LER, scram, physical security, SNM accounting.

## Task

Review nuclear plant compliance packet (LCO + LER + scram analysis + physical security + SNM inventory).

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-nuclear-safety-flags`
4. **rag_against_nrc** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/nuclear-safety-inspector
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-nuclear-safety-flags`
- **knowledge_packs**: `knowledge-pack/nuclear-nrc-iaea-frameworks`

## Success criteria

- rubric `rubric/nuclear-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/nuclear-safety-review` v0.1.0
- License: `MIT`
- Industry: nuclear, nuclear.power, nuclear.security, compliance
- Full source manifest: see `references/manifest.yaml`
