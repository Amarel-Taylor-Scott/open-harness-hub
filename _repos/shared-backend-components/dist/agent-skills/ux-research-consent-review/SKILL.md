---
name: ux-research-consent-review
description: Review UX research plans for consent, participant privacy, incentives,
  vulnerable populations, and data retention.
when_to_use: 'Pipeline kind: review.'
---

# UX Research Consent review pipeline

End-to-end ux research consent review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review UX research plans for consent, participant privacy, incentives, vulnerable populations, and data retention.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-ux-research-consent-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-ux-research-consent-retrieval-policy`
5. **review_harness** — `harness` → `harness/ux-research-consent-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/ux-research-ethics-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/ux-research-consent-frameworks`
- **rule_packs**: `rule-pack/grep-ux-research-consent-flags`, `rule-pack/rag-ux-research-consent-retrieval-policy`

## Success criteria

- rubric `rubric/ux-research-consent-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/ux-research-consent-review` v0.1.0
- License: `MIT`
- Industry: design_ops.research_ethics, privacy
- Full source manifest: see `references/manifest.yaml`
