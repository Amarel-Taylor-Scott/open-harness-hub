---
name: academic-integrity-review
description: Review a student submission for plagiarism / AI / fabricated-citation
  indicators.
when_to_use: 'Pipeline kind: review.'
---

# Academic integrity review (plagiarism / AI / citation fabrication)

Ninth vertical. Same chain — only persona / GREP / KB / rubric
change.

## Task

Review a student submission for plagiarism / AI / fabricated-citation indicators.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_integrity_flags** — `rule_pack` → `rule-pack/grep-academic-integrity-flags`
4. **rag_against_honor_codes** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/academic-integrity-officer
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-academic-integrity-flags`
- **knowledge_packs**: `knowledge-pack/academic-honor-codes`

## Success criteria

- rubric `rubric/academic-integrity-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/academic-integrity-review` v0.1.0
- License: `MIT`
- Industry: education, education.higher, compliance
- Full source manifest: see `references/manifest.yaml`
