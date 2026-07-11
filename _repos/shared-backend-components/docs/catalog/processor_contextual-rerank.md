# Contextual AI Rerank adapter (ctxl-rerank-v2-instruct — instruction-following reranker)

*processor* · `processor/contextual-rerank` · v0.1.0 · experimental

GOVERNED ADAPTER that WRAPS Contextual AI's hosted Rerank engine
(`POST /v1/rerank`, model `ctxl-rerank-v2-instruct`, +mini / +v1) as an
OpenHubForAI processor component. This is a thin wrapper over a
third-party best-of-breed engine — OHH does NOT rebuild it. Contextual's
reranker is the first instruction-following reranker: it takes a query,
a list of candidate documents, and a natural-language instruction, and
returns each candidate's index + relevance score (0-1). It is SOTA on
BEIR (61.2) and is a clearly stronger engine than OHH's local-Gemma
reranker.

WRAP, NOT REPLACE — what OHH adds ON TOP of the external engine:
  - PROVENANCE: reranked candidates retain their source_record binding
    and content hash, so the ordering that reaches the model is auditable
    back to governed sources.
  - MEASURED-LIFT ADMISSION: admitted into a pipeline only when paired
    measurement (`scripts/foundry/measure.py`) shows a positive,
    STRUCTURAL lift (`scripts/eval/reason_codes.py`) over the bare model
    — never by vendor benchmark alone. Contextual publishes engine-vs-
    engine BEIR numbers; OHH measures the lift the component adds in a
    pipeline.
  - COMPOSITION: slots into the seven-primitive grammar as a post-
    retrieval Action, interchangeable at the schema boundary with the
    local rerank path and OHH's broader retrieval family (BM25 / dense /
    hybrid / RRF fusion / MMR / GraphRAG).

DETERMINISTIC / LOCAL FALLBACK: when no Contextual credentials are
configured, the pipeline falls back to `processor/gemma-reranker`
(local Gemma via Ollama, with a deterministic BM25-order fallback that
tags results `simulated: true`). The hosted engine is stronger; the
local path keeps the pipeline shape exercisable offline.

Hosted engine, external trust boundary, external_call side effect:
routed to the external-metered worker pool (see
context/backend/architecture/component-execution-and-runtime-routing.md). Requires
a Contextual AI API key. Cost (Contextual list pricing, 2026): $0.05 per
M tokens (instruct) / $0.02 per M tokens (mini) — metered per call.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | reranking, retrieval |
| modality | text |
| lifecycle | experimental |
| trust_boundary | external |
| license | proprietary-saas-wrapped |



