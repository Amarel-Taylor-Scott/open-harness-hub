---
name: dfars-cmmc-compliance-review
description: Review defense supplier packet for DFARS / CMMC / Section 889 / counterfeit-parts
  compliance.
when_to_use: 'Pipeline kind: review.'
---

# DoD DFARS / CMMC compliance review

Vertical 22 — defense acquisition compliance.

## Task

Review defense supplier packet for DFARS / CMMC / Section 889 / counterfeit-parts compliance.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-defense-dfars-flags`
4. **rag_against_dfars** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/defense-acquisition-officer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-defense-dfars-flags`
- **knowledge_packs**: `knowledge-pack/defense-dfars-frameworks`

## Success criteria

- rubric `rubric/defense-dfars-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/dfars-cmmc-compliance-review` v0.1.0
- License: `MIT`
- Industry: defense, defense.dfars, defense.cmmc, defense.counterfeit_parts, compliance
- Full source manifest: see `references/manifest.yaml`
