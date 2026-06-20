# Hybrid label vector index

*pipeline* · `pipeline/hybrid-label-vector-index` · v0.1.0 · experimental

Combine pgvector-style embeddings with hierarchical labels, schema.org-style labels, tenant custom labels, entity links, and model-generated dimensions for flexible hybrid search.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | retrieval, classification, reranking, routing, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Emit hybrid search records by labeling and dimensioning catalog/source objects, routing model-generated label work through a provider-neutral model router, and combining labels with vector/graph index records.

**pipeline_kind:** `research_web.hybrid_label_vector_index`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_label_taxonomy` | knowledge_pack | `knowledge-pack/hybrid-label-dimension-taxonomy` | - |
| 2 | `route_label_model` | tool | `tool/model-capability-router` | - |
| 3 | `assign_labels_dimensions` | tool | `tool/hierarchical-label-dimensioner` | - |
| 4 | `emit_hybrid_index_records` | tool | `tool/index-record-emitter` | - |
| 5 | `audit` | processor | `processor/audit-trace-emitter` | - |

