---
name: ad-claims-substantiation-review
description: Review marketing claims for evidence, qualifiers, comparative claims,
  regulated terms, and approval readiness.
when_to_use: 'Pipeline kind: review.'
---

# Ad Claims Substantiation review pipeline

End-to-end ad claims substantiation review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

## Task

Review marketing claims for evidence, qualifiers, comparative claims, regulated terms, and approval readiness.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-ad-claims-substantiation-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-ad-claims-substantiation-retrieval-policy`
5. **review_harness** — `harness` → `harness/ad-claims-substantiation-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/ad-claims-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/ad-claims-substantiation-frameworks`
- **rule_packs**: `rule-pack/grep-ad-claims-substantiation-flags`, `rule-pack/rag-ad-claims-substantiation-retrieval-policy`

## Success criteria

- rubric `rubric/ad-claims-substantiation-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/ad-claims-substantiation-review` v0.1.0
- License: `MIT`
- Industry: marketing_ops, marketing_ops.claims
- Full source manifest: see `references/manifest.yaml`
