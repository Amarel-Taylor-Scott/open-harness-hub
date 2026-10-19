---
name: gov-foia-exemptions-review
description: Review public-records release packets for exemption basis, segregability,
  privacy redaction, and appeal readiness.
when_to_use: 'Pipeline kind: review.'
---

# Government FOIA Exemptions review pipeline

End-to-end government foia exemptions review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

## Task

Review public-records release packets for exemption basis, segregability, privacy redaction, and appeal readiness.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-gov-foia-exemptions-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-gov-foia-exemptions-retrieval-policy`
5. **review_harness** — `harness` → `harness/gov-foia-exemptions-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/foia-disclosure-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/gov-foia-exemptions-frameworks`
- **rule_packs**: `rule-pack/grep-gov-foia-exemptions-flags`, `rule-pack/rag-gov-foia-exemptions-retrieval-policy`

## Success criteria

- rubric `rubric/gov-foia-exemptions-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/gov-foia-exemptions-review` v0.1.0
- License: `MIT`
- Industry: government, government.foia, privacy
- Full source manifest: see `references/manifest.yaml`
