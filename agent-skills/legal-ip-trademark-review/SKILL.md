---
name: legal-ip-trademark-review
description: Review trademark clearance notes for confusion risk, goods/services proximity,
  descriptiveness, and evidence gaps.
when_to_use: 'Pipeline kind: review.'
---

# Legal IP Trademark review pipeline

End-to-end legal ip trademark review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

## Task

Review trademark clearance notes for confusion risk, goods/services proximity, descriptiveness, and evidence gaps.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-legal-ip-trademark-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-legal-ip-trademark-retrieval-policy`
5. **review_harness** — `harness` → `harness/legal-ip-trademark-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/trademark-clearance-counsel
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/legal-ip-trademark-frameworks`
- **rule_packs**: `rule-pack/grep-legal-ip-trademark-flags`, `rule-pack/rag-legal-ip-trademark-retrieval-policy`

## Success criteria

- rubric `rubric/legal-ip-trademark-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/legal-ip-trademark-review` v0.1.0
- License: `MIT`
- Industry: legal, legal.ip
- Full source manifest: see `references/manifest.yaml`
