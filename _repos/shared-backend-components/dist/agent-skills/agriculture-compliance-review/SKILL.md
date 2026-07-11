---
name: agriculture-compliance-review
description: Review agriculture compliance packet (pesticide application + water quality
  + organic OSP + worker H+S).
when_to_use: 'Pipeline kind: review.'
---

# Agriculture compliance review (FSMA + USDA NOP + GlobalGAP)

Vertical 28 — farm + packing-house compliance: FSMA water, pesticide REI/PHI/MRL, organic, child labor.

## Task

Review agriculture compliance packet (pesticide application + water quality + organic OSP + worker H+S).

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-agriculture-compliance-flags`
4. **rag_against_fsma** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/agriculture-compliance-officer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-agriculture-compliance-flags`
- **knowledge_packs**: `knowledge-pack/agriculture-compliance-frameworks`

## Success criteria

- rubric `rubric/agriculture-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/agriculture-compliance-review` v0.1.0
- License: `MIT`
- Industry: agriculture_compliance, agriculture_compliance.fsma, agriculture_compliance.organic, compliance
- Full source manifest: see `references/manifest.yaml`
