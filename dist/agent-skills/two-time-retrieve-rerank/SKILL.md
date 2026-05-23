---
name: two-time-retrieve-rerank
description: Two-pass retrieval over a corpus, with LLM-driven query refinement between
  passes and cross-encoder rerank at the end.
when_to_use: 'Pipeline kind: rag.'
---

# Two-time retrieval + cross-encoder rerank

Generic two-pass retrieval pipeline distilled from the EEDI-AWQ
shape. First-pass: retrieve top-K with the raw query. Refine the
query using LLM summary of pass-1. Second-pass: retrieve top-K' with
the refined query. Union, dedupe, cross-encoder rerank. Final
output ranked candidates.

Verified by Open Harness Hub mining of takanashihumbert "EEDI Qwen-2.5
32B AWQ two-time retrieval" (650 votes). The shape generalises to
any RAG task where the user's first query is under-specified.

## Task

Two-pass retrieval over a corpus, with LLM-driven query refinement
between passes and cross-encoder rerank at the end.

## Steps

1. **two_time** — `processor` → `processor/two-time-retrieval`
2. **rerank** — `processor` → `processor/cross-encoder-reranker`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default

## Provenance

- Hub artifact: `pipeline/two-time-retrieve-rerank` v0.1.0
- License: `MIT`
- Industry: ai, education, scientific_research
- Full source manifest: see `references/manifest.yaml`
