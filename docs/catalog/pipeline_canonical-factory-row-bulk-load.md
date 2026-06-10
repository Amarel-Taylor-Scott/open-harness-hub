# Canonical factory row bulk load

*pipeline* · `pipeline/canonical-factory-row-bulk-load` · v0.1.0 · experimental

Runs source governance, local relationship preflight, CSV bulk export, and object count reporting for generated-object rows that cover entities, dedupe, labels, dimensions, embeddings, review tickets, and index records.

| axis | value |
|---|---|
| industry | ai, software.devops, finance.aml, cross_industry |
| capability | governance, retrieval, evaluation, serving |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Prepare high-volume generated-object shards for canonical Postgres storage with relationship checks before psql bulk loading.

**pipeline_kind:** `serving`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `source-governance` | tool | `tool/source-record-governance-router` | - |
| 2 | `relationship-preflight` | tool | `tool/factory-jsonl-relationship-preflight` | - |
| 3 | `bulk-copy-export` | tool | `tool/factory-jsonl-bulk-copy-loader` | - |
| 4 | `count-staged-and-canonical` | tool | `tool/object-count-report-generator` | - |

