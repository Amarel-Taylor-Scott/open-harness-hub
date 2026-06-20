---
name: personal-search-pipeline
description: Search the user's personal corpus + emit cited answer.
when_to_use: 'Pipeline kind: rag.'
---

# Personal corpus search pipeline (RAG over user's own data)

Concrete pipeline wrapping `harness/personal-corpus-search` for
answering user queries from their own files / notes / emails /
calendar / contacts. Local-first; opt-in for hosted models.

## Task

Search the user's personal corpus + emit cited answer.

## Steps

1. **load_prefs** — `processor` → `processor/preference-loader`
2. **search** — `harness` → `harness/personal-corpus-search`
3. **leakage_check** — `rule_pack` → `rule-pack/grep-personal-info-leakage`
4. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/personal-assistant
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-personal-info-leakage`
- **knowledge_packs**: `knowledge-pack/user-preference-schema`

## Provenance

- Hub component: `pipeline/personal-search-pipeline` v0.1.0
- License: `MIT`
- Industry: personal_productivity, cross_industry
- Full source manifest: see `references/manifest.yaml`
