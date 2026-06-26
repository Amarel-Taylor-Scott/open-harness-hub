---
name: nerc-cip-compliance-review
description: Review BES cyber assets + ESP/PSP + access management against NERC CIP.
when_to_use: 'Pipeline kind: review.'
---

# NERC CIP compliance review (Bulk Electric System cyber)

Vertical 19.

## Task

Review BES cyber assets + ESP/PSP + access management against NERC CIP.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-nerc-cip-flags`
4. **rag_against_cip** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/nerc-cip-analyst
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-nerc-cip-flags`
- **knowledge_packs**: `knowledge-pack/nerc-cip-standards`

## Success criteria

- rubric `rubric/nerc-cip-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/nerc-cip-compliance-review` v0.1.0
- License: `MIT`
- Industry: energy, energy.grid, security
- Full source manifest: see `references/manifest.yaml`
