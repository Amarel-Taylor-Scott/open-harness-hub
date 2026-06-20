# Recommend an OHH pipeline (or harness / tool / etc.) from a free-text task prompt

*pipeline* · `pipeline/recommend-pipeline-from-prompt` · v0.1.0 · experimental

Given a user's natural-language task description, return the best
catalog components to use, ranked with rationale and a usage hint.

Three-stage shape:
 1. `processor/catalog-search`   — BM25 + tag Jaccard → top 30
 2. `processor/gemma-reranker`   — Gemma 4 (or any LLM) → top 5
 3. `processor/pipeline-recommender` — composition sketch

Use cases:
 - User typing "I need to grade an ESG supplier disclosure" → returns
   `pipeline/supplier-policy-grading` + `harness/esg-disclosure-grading`
 - User typing "I want to review a Wikipedia article for NPOV" →
   returns `pipeline/wikipedia-page-review`
 - Codex orchestrator deciding which existing pipeline to invoke
   before falling back to factory drafting

Output: ranked candidates with per-candidate score + reason,
recommendation paragraph, composition hints (how to actually use
the top recommendation).

| axis | value |
|---|---|
| industry | software, ai, cross_industry |
| capability | retrieval, reranking, reasoning |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given a free-text task prompt, return the best OHH catalog component(s)
to use to accomplish the task, with per-candidate rationale and a
composition hint for the top match.

**pipeline_kind:** `recommendation`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `search` | processor | `processor/catalog-search` | - |
| 2 | `rerank` | processor | `processor/gemma-reranker` | - |
| 3 | `recommend` | processor | `processor/pipeline-recommender` | - |
| 4 | `audit` | processor | `processor/audit-trace-emitter` | - |

