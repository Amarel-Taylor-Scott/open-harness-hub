---
name: deep-research-supervisor-workers
description: Given a research query, dispatch parallel research workers each scoped
  to a sub-topic, compress their findings, write a synthesized report with citations.
when_to_use: 'Pipeline kind: research_web.'
---

# Deep research: supervisor + parallel workers

LangChain's open_deep_research pattern. A supervisor LLM decomposes
the user query into research briefs and dispatches N parallel
researcher subagents (each gets its own context + tools), then
compresses and writes the final report.

Verified by Open Harness Hub clone:
`langchain-ai/open_deep_research/src/open_deep_research/deep_researcher.py`
(~700 LOC) + `prompts.py`.

## Task

Given a research query, dispatch parallel research workers each
scoped to a sub-topic, compress their findings, write a synthesized
report with citations.

## Steps

1. **redact_query** — `harness` → `harness/redact-pii-text`
2. **clarify** — `harness` → `harness/text-safety-review`
3. **brief_writer** — `harness` → `harness/text-safety-review`
4. **decompose_to_workers** — `processor` → `processor/sub-question-decomposer`
5. **dispatch_workers** — `harness` → `harness/text-safety-review`
6. **compress_notes** — `processor` → `processor/llmlingua-context-compressor`
7. **write_report** — `harness` → `harness/text-safety-review`
8. **verify_citations** — `processor` → `processor/citation-coverage`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/privacy-pii-text-en`, `rule-pack/web-search-allowlist-default`

## Success criteria

- rubric `rubric/research-entity-v1` threshold 0.8

## Provenance

- Hub artifact: `pipeline/deep-research-supervisor-workers` v0.1.0
- License: `MIT`
- Industry: ai, media, cross_industry
- Full source manifest: see `references/manifest.yaml`
