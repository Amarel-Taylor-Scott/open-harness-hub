# Embedding committed load audit

*pipeline* · `pipeline/embedding-committed-load-audit` · v0.1.0 · experimental

Compares planned embeddings, stored vectors, pgvector load evidence, and Postgres committed counts to gate vector search readiness.

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

Gate tenant-visible vector search on committed Postgres object_embedding counts after embedding load planning.

**pipeline_kind:** `research_web.embedding_committed_load_audit`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-embedding-commit-checks` | knowledge_pack | `knowledge-pack/embedding-committed-load-audit-patterns` | - |
| 2 | `audit-embedding-committed-load` | tool | `tool/embedding-committed-load-auditor` | - |

