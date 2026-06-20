# Gemma 4 post-RAG reranker (stage 2 of pipeline recommendation)

*processor* · `processor/gemma-reranker` · v0.1.0 · experimental

Lightweight LLM-based reranker that takes a small candidate set
(typically top 20-30 from `processor/catalog-search`) plus a user
prompt, and re-orders the candidates by relevance using a small
local model. Default: Gemma 4 via Ollama; any chat-capable adapter
works (set OH_RERANK_MODEL or pass model id explicitly).

The reranker emits a STRUCTURED RANKING with per-candidate score +
one-sentence rationale, plus an overall recommendation paragraph.
Structure lets downstream code use the ranking programmatically and
lets a human read the rationale.

Falls back gracefully to DETERMINISTIC SIMULATION when no model is
reachable (Ollama down, env not set), preserving the initial BM25
order and tagging results with `simulated: true`. This means the
pipeline shape exercises without LLM cost during CI / offline runs.

Stage 2 of the recommend-from-prompt flow:
 - stage 1: `processor/catalog-search` (BM25 + Jaccard)
 - stage 2: `processor/gemma-reranker` (this)
 - stage 3: `processor/pipeline-recommender` (composition sketch)

| axis | value |
|---|---|
| industry | software, ai, cross_industry |
| capability | reranking, evaluation, reasoning |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



