# Local blueprint records to Postgres JSONL

*pipeline* · `pipeline/local-blueprint-records-to-postgres-jsonl` · v0.1.0 · experimental

Exports local sentence-to-pipeline demo output records into canonical JSONL row families and prepares them for the existing Postgres bulk-copy loader.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | format_conversion, retrieval, governance, planning |
| modality | text, image, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



## Task

Convert a local sentence-to-pipeline run into canonical source, object, entity, dedupe, review, and index JSONL shards that can be loaded into Postgres/pgvector.

**pipeline_kind:** `meta_build.local_blueprint_persistence`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-source-prompt` | tool | `tool/source-record-governance-router` | - |
| 2 | `run-local-demo` | tool | `tool/sentence-to-pipeline-blueprint-runner` | - |
| 3 | `emit-output-records` | pipeline | `pipeline/local-sentence-blueprint-output-records` | - |
| 4 | `export-jsonl-row-families` | tool | `tool/blueprint-record-jsonl-exporter` | - |
| 5 | `preflight-row-relationships` | tool | `tool/factory-jsonl-relationship-preflight` | - |
| 6 | `prepare-bulk-copy` | tool | `tool/factory-jsonl-bulk-copy-loader` | - |

