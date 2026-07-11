---
name: telco-compliance-review
description: Review telecom carrier compliance packet (CPNI handling + NORS outages
  + STIR/SHAKEN + CALEA + E911).
when_to_use: 'Pipeline kind: review.'
---

# Telco compliance review (FCC + CPNI + CALEA + STIR/SHAKEN)

Vertical 25 — telecom-carrier compliance: CPNI breach, NORS outages, STIR/SHAKEN, CALEA, E911.

## Task

Review telecom carrier compliance packet (CPNI handling + NORS outages + STIR/SHAKEN + CALEA + E911).

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-telco-compliance-flags`
4. **rag_against_fcc** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/telco-compliance-officer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-telco-compliance-flags`
- **knowledge_packs**: `knowledge-pack/telco-fcc-cpni-frameworks`

## Success criteria

- rubric `rubric/telco-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/telco-compliance-review` v0.1.0
- License: `MIT`
- Industry: telecommunications, telecommunications.fcc, telecommunications.cpni, compliance
- Full source manifest: see `references/manifest.yaml`
