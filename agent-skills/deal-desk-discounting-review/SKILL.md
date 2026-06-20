---
name: deal-desk-discounting-review
description: Review discount and commercial exception packets for approval authority,
  margin impact, and precedent risk.
when_to_use: 'Pipeline kind: review.'
---

# Deal Desk Discounting review pipeline

End-to-end deal desk discounting review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review discount and commercial exception packets for approval authority, margin impact, and precedent risk.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-deal-desk-discounting-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-deal-desk-discounting-retrieval-policy`
5. **review_harness** — `harness` → `harness/deal-desk-discounting-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/deal-desk-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/deal-desk-discounting-frameworks`
- **rule_packs**: `rule-pack/grep-deal-desk-discounting-flags`, `rule-pack/rag-deal-desk-discounting-retrieval-policy`

## Success criteria

- rubric `rubric/deal-desk-discounting-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/deal-desk-discounting-review` v0.1.0
- License: `MIT`
- Industry: sales_ops.discounting, legal.contract
- Full source manifest: see `references/manifest.yaml`
