---
name: ai-governance-audit
description: Audit AI system for EU AI Act + NIST + ISO 42001 conformity.
when_to_use: 'Pipeline kind: review.'
---

# AI governance audit (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)

Vertical 33 — AI conformity assessment for Annex III high-risk + GPAI + ISO 42001 AIMS.

## Task

Audit AI system for EU AI Act + NIST + ISO 42001 conformity.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_red_flags** — `rule_pack` → `rule-pack/grep-ai-governance-flags`
4. **rag_against_act** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/ai-governance-auditor
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-ai-governance-flags`
- **knowledge_packs**: `knowledge-pack/ai-governance-frameworks`

## Success criteria

- rubric `rubric/ai-governance-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/ai-governance-audit` v0.1.0
- License: `MIT`
- Industry: ai_governance, ai_governance.eu_act, ai_governance.nist_rmf, ai_governance.iso_42001, privacy, compliance
- Full source manifest: see `references/manifest.yaml`
