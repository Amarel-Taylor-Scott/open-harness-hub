# Pgvector embedding load plan

*pipeline* · `pipeline/pgvector-embedding-load-plan` · v0.1.0 · experimental

Turns stored vector JSONL rows into accepted/rejected load evidence and reviewable SQL for the canonical Postgres object_embedding table.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | embedding, retrieval, governance, evaluation |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Convert completed local embedding worker vector rows into reviewable pgvector object_embedding load SQL.

**pipeline_kind:** `research_web.pgvector_embedding_load_plan`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-pgvector-load-checks` | knowledge_pack | `knowledge-pack/pgvector-embedding-load-patterns` | - |
| 2 | `plan-pgvector-embedding-load` | tool | `tool/pgvector-embedding-load-planner` | - |

