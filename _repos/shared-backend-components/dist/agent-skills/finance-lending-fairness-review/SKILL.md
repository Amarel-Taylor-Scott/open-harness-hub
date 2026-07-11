---
name: finance-lending-fairness-review
description: Review lending decision packets for adverse-action reasons, fair-lending
  proxy risk, documentation sufficiency, and escalation needs.
when_to_use: 'Pipeline kind: review.'
---

# Finance Lending Fairness review pipeline

End-to-end finance lending fairness review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

## Task

Review lending decision packets for adverse-action reasons, fair-lending proxy risk, documentation sufficiency, and escalation needs.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-finance-lending-fairness-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-finance-lending-fairness-retrieval-policy`
5. **review_harness** — `harness` → `harness/finance-lending-fairness-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/fair-lending-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/finance-lending-fairness-frameworks`
- **rule_packs**: `rule-pack/grep-finance-lending-fairness-flags`, `rule-pack/rag-finance-lending-fairness-retrieval-policy`

## Success criteria

- rubric `rubric/finance-lending-fairness-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/finance-lending-fairness-review` v0.1.0
- License: `MIT`
- Industry: finance, finance.lending, compliance
- Full source manifest: see `references/manifest.yaml`
