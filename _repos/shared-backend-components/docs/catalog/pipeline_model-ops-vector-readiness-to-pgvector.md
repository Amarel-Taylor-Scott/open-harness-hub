# Model ops vector readiness to pgvector

*pipeline* · `pipeline/model-ops-vector-readiness-to-pgvector` · v0.1.0 · experimental

Plans embeddings, runs a local deterministic embedding worker, emits pgvector load SQL, and audits committed-load readiness for a staged model-ops daily run.

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

Move a staged model-ops daily run from embedding work rows to pgvector-ready load SQL and a committed-load audit, without applying SQL or marking vector search product-ready.

**pipeline_kind:** `research_web.model_ops_vector_readiness_to_pgvector`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `plan-embedding-execution` | tool | `tool/embedding-execution-planner` | - |
| 2 | `run-local-hash-worker` | tool | `tool/local-hash-embedding-worker` | - |
| 3 | `plan-pgvector-load` | tool | `tool/pgvector-embedding-load-planner` | - |
| 4 | `audit-committed-load` | tool | `tool/embedding-committed-load-auditor` | - |

