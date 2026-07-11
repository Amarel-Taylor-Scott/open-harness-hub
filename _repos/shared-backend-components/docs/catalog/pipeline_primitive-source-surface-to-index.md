# Primitive source surface to index

*pipeline* · `pipeline/primitive-source-surface-to-index` · v0.1.0 · experimental

Scan source surfaces, normalize candidate primitives, apply verified-source rules, and prepare records for keyword, vector, graph, and model-polished search.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | retrieval, planning, evaluation, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Convert routine source-surface scans and verified-source submissions into indexed candidate primitives for search and blueprint generation.

**pipeline_kind:** `research_web.primitive_index_build`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_source_surfaces` | knowledge_pack | `knowledge-pack/primitive-source-surface-map` | - |
| 2 | `scan_surfaces` | tool | `tool/primitive-source-surface-scanner` | - |
| 3 | `verified_source_intake` | tool | `tool/verified-source-publisher-intake` | - |
| 4 | `normalize_records` | tool | `tool/search-result-normalizer` | - |
| 5 | `score_gap_signals` | tool | `tool/capability-gap-signal-scorer` | - |
| 6 | `semantic_catalog_dedupe` | tool | `tool/embedding-index-search` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

