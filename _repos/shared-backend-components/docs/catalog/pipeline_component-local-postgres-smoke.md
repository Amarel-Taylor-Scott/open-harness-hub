# Component local Postgres smoke

*pipeline* · `pipeline/component-local-postgres-smoke` · v0.1.0 · experimental

Builds a reviewed local Docker pgvector smoke plan for loading staged component rows and embedding vectors, then rerunning committed-count audits.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | retrieval, embedding, governance, evaluation, serving |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Emit a side-effect-free local Postgres smoke plan that applies candidate row SQL and vector SQL only after operator review, then proves committed candidate and embedding counts.

**pipeline_kind:** `research_web.component_local_postgres_smoke`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `plan-component-local-postgres-smoke` | tool | `tool/component-local-postgres-smoke-planner` | - |

