# Local embedding worker contract smoke

*pipeline* · `pipeline/local-embedding-worker-contract-smoke` · v0.1.0 · experimental

Runs a bounded local worker contract check that proves stored vector metadata rows line up with daily embedding completion stubs.

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

Prove a local embedding worker can produce database-loadable vector metadata rows for a daily embedding execution sample.

**pipeline_kind:** `research_web.local_embedding_worker_contract_smoke`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-local-embedding-contract-checks` | knowledge_pack | `knowledge-pack/local-embedding-worker-contract-patterns` | - |
| 2 | `run-local-embedding-worker-contract` | tool | `tool/local-embedding-worker-contract` | - |

