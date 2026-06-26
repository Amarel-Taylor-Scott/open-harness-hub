---
name: marketing-consent-governance-review
description: Review campaign packets for consent basis, preference handling, suppression
  lists, and unsubscribe controls.
when_to_use: 'Pipeline kind: review.'
---

# Marketing Consent Governance review pipeline

End-to-end marketing consent governance review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review campaign packets for consent basis, preference handling, suppression lists, and unsubscribe controls.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-marketing-consent-governance-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-marketing-consent-governance-retrieval-policy`
5. **review_harness** — `harness` → `harness/marketing-consent-governance-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/marketing-consent-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/marketing-consent-governance-frameworks`
- **rule_packs**: `rule-pack/grep-marketing-consent-governance-flags`, `rule-pack/rag-marketing-consent-governance-retrieval-policy`

## Success criteria

- rubric `rubric/marketing-consent-governance-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/marketing-consent-governance-review` v0.1.0
- License: `MIT`
- Industry: marketing_ops.consent, privacy
- Full source manifest: see `references/manifest.yaml`
