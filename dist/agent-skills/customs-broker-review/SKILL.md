---
name: customs-broker-review
description: Review customs entry packet (ISF + HTS + valuation + FTA preference +
  UFLPA + AD/CVD risk).
when_to_use: 'Pipeline kind: review.'
---

# Customs entry review (US CBP + UFLPA + USMCA + WCO)

Vertical 29 — customs-entry compliance: ISF 10+2, HTS classification, FTA origin, UFLPA, AD/CVD.

## Task

Review customs entry packet (ISF + HTS + valuation + FTA preference + UFLPA + AD/CVD risk).

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-customs-broker-flags`
4. **rag_against_cbp** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/customs-broker
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-customs-broker-flags`
- **knowledge_packs**: `knowledge-pack/customs-cbp-wco-frameworks`

## Success criteria

- rubric `rubric/customs-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/customs-broker-review` v0.1.0
- License: `MIT`
- Industry: customs, customs.entry, customs.tariff, customs.fta, trade, compliance
- Full source manifest: see `references/manifest.yaml`
