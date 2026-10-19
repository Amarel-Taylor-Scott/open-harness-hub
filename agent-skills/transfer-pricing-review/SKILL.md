---
name: transfer-pricing-review
description: Review intercompany transactions for arm's-length compliance + Pillar
  Two ETR exposure.
when_to_use: 'Pipeline kind: review.'
---

# Transfer pricing review (OECD TPG / BEPS / §482 / Pillar Two)

Vertical 21.

## Task

Review intercompany transactions for arm's-length compliance + Pillar Two ETR exposure.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-transfer-pricing-flags`
4. **rag_against_oecd** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/transfer-pricing-counsel
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-transfer-pricing-flags`
- **knowledge_packs**: `knowledge-pack/oecd-tp-and-beps`

## Success criteria

- rubric `rubric/transfer-pricing-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/transfer-pricing-review` v0.1.0
- License: `MIT`
- Industry: tax, tax.transfer_pricing, finance
- Full source manifest: see `references/manifest.yaml`
