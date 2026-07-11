# Postgres load execution and audit

*pipeline* · `pipeline/postgres-load-execution-and-audit` · v0.1.0 · experimental

Creates a side-effect-free command plan to initialize Postgres/pgvector, apply a generated bulk load, export committed counts, and audit staged versus committed object rows.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, retrieval, serving, evaluation, verification |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Plan execution of a generated object-factory load.sql against Postgres and the follow-up committed-count audit.

**pipeline_kind:** `research_web.postgres_load_execution`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-load-execution-plan` | tool | `tool/source-record-governance-router` | - |
| 2 | `emit-execution-plan` | tool | `tool/postgres-load-execution-planner` | - |
| 3 | `convert-counts-after-psql` | tool | `tool/psql-csv-count-json-converter` | psql count CSV is available |
| 4 | `audit-after-load` | tool | `tool/staged-vs-committed-load-auditor` | committed count JSON is available |

