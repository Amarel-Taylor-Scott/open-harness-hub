---
name: media-claims-factcheck-review
description: Review article claims for source quality, quote fidelity, unsupported
  assertions, and correction risk.
when_to_use: 'Pipeline kind: review.'
---

# Media Claims Factcheck review pipeline

End-to-end media claims factcheck review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

## Task

Review article claims for source quality, quote fidelity, unsupported assertions, and correction risk.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-media-claims-factcheck-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-media-claims-factcheck-retrieval-policy`
5. **review_harness** — `harness` → `harness/media-claims-factcheck-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/claims-factcheck-editor
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/media-claims-factcheck-frameworks`
- **rule_packs**: `rule-pack/grep-media-claims-factcheck-flags`, `rule-pack/rag-media-claims-factcheck-retrieval-policy`

## Success criteria

- rubric `rubric/media-claims-factcheck-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/media-claims-factcheck-review` v0.1.0
- License: `MIT`
- Industry: media, media.factcheck
- Full source manifest: see `references/manifest.yaml`
