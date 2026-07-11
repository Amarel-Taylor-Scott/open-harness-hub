# Source governance entity dedupe index

*pipeline* · `pipeline/source-governance-entity-dedupe-index` · v0.1.0 · experimental

Normalize source records, apply governance routing, extract and link entities, fuzzy-dedupe objects, and emit keyword, vector, graph, facet, freshness, and review records.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, verification, extraction, retrieval, routing |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Prepare raw source records and extracted objects for scalable, trustworthy indexing by applying governance, entity linking, deduplication, and index record emission.

**pipeline_kind:** `research_web.source_governance_entity_dedupe_index`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `route_source_governance` | tool | `tool/source-record-governance-router` | - |
| 2 | `link_entities` | tool | `tool/entity-recognition-linker` | - |
| 3 | `dedupe_candidates` | tool | `tool/fuzzy-dedupe-clusterer` | - |
| 4 | `emit_index_records` | tool | `tool/index-record-emitter` | - |
| 5 | `audit` | processor | `processor/audit-trace-emitter` | - |

