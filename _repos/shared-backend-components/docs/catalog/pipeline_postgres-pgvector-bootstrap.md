# Postgres pgvector bootstrap

*pipeline* · `pipeline/postgres-pgvector-bootstrap` · v0.1.0 · experimental

Plans and executes the canonical Postgres/pgvector bootstrap path for generated object storage, loader SQL application, and object count reporting.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, retrieval, serving, evaluation |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | stable |
| license | MIT |



## Task

Bootstrap a canonical Postgres/pgvector store for generated OpenHubForAI objects and report database-backed object counts.

**pipeline_kind:** `serving`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `plan-bootstrap` | tool | `tool/postgres-pgvector-bootstrap-planner` | - |
| 2 | `emit-loader-sql` | tool | `tool/factory-jsonl-postgres-loader` | - |
| 3 | `count-canonical-rows` | tool | `tool/postgres-object-count-sql` | database_url is present |
| 4 | `count-staged-rows` | tool | `tool/object-count-report-generator` | - |

