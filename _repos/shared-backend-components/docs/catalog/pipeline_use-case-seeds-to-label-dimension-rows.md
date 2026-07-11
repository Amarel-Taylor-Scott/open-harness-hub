# Use case seeds to label and dimension rows

*pipeline* · `pipeline/use-case-seeds-to-label-dimension-rows` · v0.1.0 · experimental

Exports broad use-case seeds into candidate primitive rows, flexible hierarchy labels, dimensions, canonical entities, object_entity_refs, object_embedding stubs, dedupe clusters, review tickets, and index records for Postgres/pgvector loading.

| axis | value |
|---|---|
| industry | ai, software.devops, finance, legal, media, creative, energy, healthcare, cross_industry |
| capability | classification, extraction, retrieval, routing, governance |
| modality | text, image, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | stable |
| license | MIT |



## Task

Convert cross-domain use-case seeds into loadable candidate primitive, label, dimension, dedupe, review, and index JSONL row families while excluding insurance scope.

**pipeline_kind:** `research_web.use_case_seed_label_dimension_rows`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-use-case-seeds` | tool | `tool/source-record-governance-router` | - |
| 2 | `export-seed-row-families` | tool | `tool/use-case-seed-row-exporter` | - |
| 3 | `link-seed-entities` | tool | `tool/entity-recognition-linker` | - |
| 4 | `preflight-row-relationships` | tool | `tool/factory-jsonl-relationship-preflight` | - |
| 5 | `prepare-bulk-copy` | tool | `tool/factory-jsonl-bulk-copy-loader` | - |

