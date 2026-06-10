# Local hash embedding worker smoke

*pipeline* · `pipeline/local-hash-embedding-worker-smoke` · v0.1.0 · experimental

Runs a deterministic local embedding worker against a daily embedding execution sample and validates the emitted vector rows.

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

Generate local deterministic vectors for a daily embedding execution sample and prove the stored rows pass vector readiness.

**pipeline_kind:** `research_web.local_hash_embedding_worker_smoke`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-local-hash-worker-checks` | knowledge_pack | `knowledge-pack/local-hash-embedding-worker-patterns` | - |
| 2 | `run-local-hash-embedding-worker` | tool | `tool/local-hash-embedding-worker` | - |

