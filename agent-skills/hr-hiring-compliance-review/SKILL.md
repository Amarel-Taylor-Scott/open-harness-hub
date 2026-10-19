---
name: hr-hiring-compliance-review
description: Review a job posting / screening process for protected-class bias + disparate
  impact.
when_to_use: 'Pipeline kind: review.'
---

# HR hiring compliance review (EEOC / Title VII / ADA / ADEA)

Twelfth vertical.

## Task

Review a job posting / screening process for protected-class bias + disparate impact.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_bias_flags** — `rule_pack` → `rule-pack/grep-hr-hiring-bias-flags`
4. **rag_against_statutes** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/eeoc-hiring-officer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-hr-hiring-bias-flags`
- **knowledge_packs**: `knowledge-pack/eeoc-hiring-statutes`

## Success criteria

- rubric `rubric/hr-hiring-compliance-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/hr-hiring-compliance-review` v0.1.0
- License: `MIT`
- Industry: hr, hr.hiring, compliance
- Full source manifest: see `references/manifest.yaml`
