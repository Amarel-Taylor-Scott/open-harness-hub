# Partitioned JSONL to index delta

*pipeline* · `pipeline/partitioned-jsonl-to-index-delta` · v0.1.0 · experimental

Convert high-volume normalized-object JSONL shards into partition manifests and append-only index deltas for keyword, vector, graph, facet, quality, freshness, and cost stores.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | retrieval, governance, serving, format_conversion |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Emit replayable partition manifests and index deltas from normalized object JSONL shards so large-scale ingestion can update search/vector/graph stores without rebuilding the whole catalog.

**pipeline_kind:** `research_web.partitioned_jsonl_to_index_delta`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_partition_patterns` | knowledge_pack | `knowledge-pack/partitioned-index-delta-patterns` | - |
| 2 | `emit_partition_delta` | tool | `tool/partition-index-delta-emitter` | - |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | - |

