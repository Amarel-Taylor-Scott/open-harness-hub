---
name: rcra-waste-review
description: Review RCRA hazardous waste generator / TSDF compliance packet.
when_to_use: 'Pipeline kind: review.'
---

# RCRA hazardous waste review (40 CFR 260-279 + e-Manifest + DOT HMR)

Vertical 34 — LQG/SQG/TSDF + Universal Waste compliance.

## Task

Review RCRA hazardous waste generator / TSDF compliance packet.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-rcra-waste-flags`
4. **rag_against_rcra** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/rcra-waste-manager
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-rcra-waste-flags`
- **knowledge_packs**: `knowledge-pack/rcra-waste-frameworks`

## Success criteria

- rubric `rubric/rcra-waste-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/rcra-waste-review` v0.1.0
- License: `MIT`
- Industry: waste, waste.rcra_tsdf, waste.generator, waste.universal, compliance
- Full source manifest: see `references/manifest.yaml`
