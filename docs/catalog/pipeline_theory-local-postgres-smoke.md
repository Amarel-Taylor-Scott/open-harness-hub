# Theory local Postgres smoke

*pipeline* · `pipeline/theory-local-postgres-smoke` · v0.1.0 · experimental

Creates an operator-reviewed local pgvector execution plan for loading theory-derived component candidates and vectors, then rerunning committed-count audits.

| axis | value |
|---|---|
| industry | ai, software.devops, security.defensive, cross_industry |
| capability | governance, embedding, planning, evaluation |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Bridge theory-derived staged rows and vectors into reviewed local Postgres smoke commands.

**pipeline_kind:** `research_web.theory_local_postgres_smoke`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `build-local-postgres-smoke-plan` | tool | `tool/theory-local-postgres-smoke-planner` | - |
| 2 | `audit` | processor | `processor/audit-trace-emitter` | - |

