---
name: benefits-adjudication-review
description: Review a benefits application + supporting docs; determine eligibility
  + benefit amount + missing-docs + appeal-rights.
when_to_use: 'Pipeline kind: review.'
---

# Government benefits adjudication review (SNAP / Medicaid / UI / SSI)

Tenth vertical. Same 6-step chain — persona / GREP / KB / rubric
swap for benefits-eligibility adjudication.

## Task

Review a benefits application + supporting docs; determine eligibility + benefit amount + missing-docs + appeal-rights.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-benefits-eligibility-flags`
4. **rag_against_rules** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/benefits-adjudicator
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-benefits-eligibility-flags`
- **knowledge_packs**: `knowledge-pack/gov-benefits-rules`

## Success criteria

- rubric `rubric/benefits-adjudication-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/benefits-adjudication-review` v0.1.0
- License: `MIT`
- Industry: government, government.benefits, compliance
- Full source manifest: see `references/manifest.yaml`
