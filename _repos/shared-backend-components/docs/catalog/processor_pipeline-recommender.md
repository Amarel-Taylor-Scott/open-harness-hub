# Pipeline recommender (end-to-end orchestrator: search → rerank → sketch)

*processor* · `processor/pipeline-recommender` · v0.1.0 · experimental

End-to-end orchestrator for "I need a pipeline to do XYZ":

 1. processor/catalog-search    — BM25 + Jaccard → top 30
 2. processor/gemma-reranker    — Gemma 4 rerank → top 5 + rationale
 3. heuristic composition-sketch — "use X with Y; pipe to Z"

Returns a single dict with all three stages plus a usage hint based
on the top candidate's component type.

CLI usage (also embeddable as a processor in larger pipelines):

  python -m scripts.processors.pipeline_recommender \\
      --prompt "I need a pipeline to grade an ESG supplier disclosure"

Pairs with `pipeline/recommend-pipeline-from-prompt` for a manifest-
declared invocation.

| axis | value |
|---|---|
| industry | software, ai, cross_industry |
| capability | retrieval, reranking, reasoning |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



