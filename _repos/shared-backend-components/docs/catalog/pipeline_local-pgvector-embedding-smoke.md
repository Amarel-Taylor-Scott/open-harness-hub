# Local pgvector embedding smoke

*pipeline* · `pipeline/local-pgvector-embedding-smoke` · v0.1.0 · experimental

Builds a side-effect-free operator plan for smoke testing embedding load SQL against the local Docker pgvector database.

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

Emit a reviewed local pgvector smoke execution plan for embedding load SQL and committed-count audits.

**pipeline_kind:** `research_web.local_pgvector_embedding_smoke`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-local-pgvector-smoke-checks` | knowledge_pack | `knowledge-pack/local-pgvector-embedding-smoke-patterns` | - |
| 2 | `plan-local-pgvector-embedding-smoke` | tool | `tool/local-pgvector-embedding-smoke-planner` | - |

