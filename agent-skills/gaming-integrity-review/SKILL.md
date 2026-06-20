---
name: gaming-integrity-review
description: Review gaming operator compliance packet (CTR/SAR filings + self-exclusion
  + SOF + match-fixing monitoring).
when_to_use: 'Pipeline kind: review.'
---

# Gaming integrity review (BSA AML + responsible-gambling + match-fixing)

Vertical 26 — gaming-operator review: AML/CTR/SAR, self-exclusion, source-of-funds, match-fixing.

## Task

Review gaming operator compliance packet (CTR/SAR filings + self-exclusion + SOF + match-fixing monitoring).

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-gaming-integrity-flags`
4. **rag_against_bsa** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/gaming-integrity-officer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-gaming-integrity-flags`
- **knowledge_packs**: `knowledge-pack/gaming-aml-rg-frameworks`

## Success criteria

- rubric `rubric/gaming-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/gaming-integrity-review` v0.1.0
- License: `MIT`
- Industry: gaming, gaming.aml, gaming.responsible, compliance
- Full source manifest: see `references/manifest.yaml`
