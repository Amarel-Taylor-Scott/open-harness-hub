# Specialized model-card rows to load plan

*pipeline* · `pipeline/specialized-model-card-rows-to-load-plan` · v0.1.0 · experimental

Preflights specialized model-card row families, scores promotion readiness, emits review tickets and quality index rows, and exports a Postgres/pgvector bulk-load package.

| axis | value |
|---|---|
| industry | healthcare, finance, legal, software.devops, media, security, privacy, government, cross_industry |
| capability | governance, evaluation, retrieval, routing, serving, embedding |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Create a review-gated Postgres/pgvector load plan from specialized model-card row families.

**pipeline_kind:** `research_web.specialized_model_card_load_plan`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-load-plan-inputs` | tool | `tool/source-record-governance-router` | - |
| 2 | `emit-load-plan` | tool | `tool/specialized-model-card-load-plan-emitter` | - |
| 3 | `route-load-review` | tool | `tool/object-factory-job-router` | - |

