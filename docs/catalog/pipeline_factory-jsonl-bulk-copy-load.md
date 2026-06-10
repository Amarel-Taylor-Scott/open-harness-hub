# Factory JSONL bulk COPY load

*pipeline* · `pipeline/factory-jsonl-bulk-copy-load` · v0.1.0 · experimental

Converts validated generated-object JSONL shards into CSV staging files and a psql bulk load script for canonical Postgres storage.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, retrieval, serving, evaluation |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Bulk-load high-volume generated Open Harness Hub objects into canonical Postgres tables without inflating YAML manifests.

**pipeline_kind:** `serving`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `privacy-and-source-gate` | tool | `tool/source-record-governance-router` | - |
| 2 | `export-bulk-copy` | tool | `tool/factory-jsonl-bulk-copy-loader` | - |
| 3 | `count-staged-rows` | tool | `tool/object-count-report-generator` | - |
| 4 | `count-canonical-rows` | tool | `tool/postgres-object-count-sql` | database_url is present |

