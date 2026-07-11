# Source surface seeds to factory rows

*pipeline* · `pipeline/source-surface-seeds-to-factory-rows` · v0.1.0 · experimental

Converts esoteric industry source-surface seeds into canonical factory row families with source governance, entity refs, fuzzy dedupe, embedding stubs, review tickets, and index records.

| axis | value |
|---|---|
| industry | automotive, energy, manufacturing, construction, government, cross_industry |
| capability | extraction, classification, retrieval, governance, evaluation |
| modality | text, image, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | stable |
| license | MIT |



## Task

Export source-surface seeds into canonical JSONL row families ready for relationship preflight and Postgres bulk-copy loading.

**pipeline_kind:** `research_web.source_surface_seed_factory_rows`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-source-surface-seeds` | tool | `tool/source-record-governance-router` | - |
| 2 | `export-source-surface-row-families` | tool | `tool/source-surface-seed-row-exporter` | - |
| 3 | `preflight-row-relationships` | tool | `tool/factory-jsonl-relationship-preflight` | - |
| 4 | `prepare-bulk-copy` | tool | `tool/factory-jsonl-bulk-copy-loader` | - |

