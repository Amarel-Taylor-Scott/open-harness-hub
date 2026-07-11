# Embedding execution plan

*pipeline* · `pipeline/embedding-execution-plan` · v0.1.0 · experimental

Plans embedding batches from staged object_embedding rows, routes them by local or external model profile, estimates cost where possible, and emits completion stubs for later vector readiness audits.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | retrieval, embedding, governance, evaluation, serving |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | stable |
| license | MIT |



## Task

Turn staged object_embedding rows into auditable embedding execution batches without calling embedding providers.

**pipeline_kind:** `research_web.embedding_execution_plan`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-embedding-inputs` | tool | `tool/source-record-governance-router` | - |
| 2 | `lookup-embedding-pricing` | tool | `tool/model-pricing-lookup` | external embedding profile is selected |
| 3 | `plan-embedding-batches` | tool | `tool/embedding-execution-planner` | - |
| 4 | `route-to-vector-store` | tool | `tool/postgres-load-execution-planner` | - |

