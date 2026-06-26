---
name: water-utility-compliance-review
description: Review Public Water System compliance packet (operations + monitoring
  + LSL inventory + RRA/ERP + SCADA cyber).
when_to_use: 'Pipeline kind: review.'
---

# Water utility compliance review (SDWA / NPDWR / LCRR / AWIA)

Vertical 24 — drinking-water utility compliance + cyber.

## Task

Review Public Water System compliance packet (operations + monitoring + LSL inventory + RRA/ERP + SCADA cyber).

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-water-utility-flags`
4. **rag_against_sdwa** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/water-utility-compliance-officer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-water-utility-flags`
- **knowledge_packs**: `knowledge-pack/water-sdwa-lcrr-awia`

## Success criteria

- rubric `rubric/water-utility-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/water-utility-compliance-review` v0.1.0
- License: `MIT`
- Industry: water_utility, water_utility.sdwa, water_utility.lcr, water_utility.scada, compliance
- Full source manifest: see `references/manifest.yaml`
