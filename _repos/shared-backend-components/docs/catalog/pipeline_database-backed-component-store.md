# Database-backed component store

*pipeline* · `pipeline/database-backed-component-store` · v0.1.0 · experimental

Routes generated factory rows into a Postgres-first component and subcomponent store plan, preserving source governance, dedupe, indexing, review, and search readiness gates.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, retrieval, serving, verification |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | stable |
| license | MIT |



## Task

Plan canonical database rows for active components and subcomponents from governed factory output.

**pipeline_kind:** `research_web.database_backed_component_store`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-source-rows` | tool | `tool/source-record-governance-router` | - |
| 2 | `plan-component-store` | tool | `tool/component-store-planner` | - |
| 3 | `preflight-relationships` | tool | `tool/factory-jsonl-relationship-preflight` | - |
| 4 | `route-review` | tool | `tool/object-factory-job-router` | - |

