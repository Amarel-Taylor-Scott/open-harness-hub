# Staged versus committed load audit

*pipeline* · `pipeline/staged-vs-committed-load-audit` · v0.1.0 · experimental

Compares object-factory staged bulk-load counts against canonical Postgres and pgvector row counts to prove what was actually committed after load execution.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, evaluation, retrieval, serving, verification |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Audit whether staged object-factory rows from a load plan match canonical Postgres row counts after load execution.

**pipeline_kind:** `research_web.staged_vs_committed_load_audit`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-load-audit-inputs` | tool | `tool/source-record-governance-router` | - |
| 2 | `run-postgres-count-report` | tool | `tool/postgres-object-count-sql` | database_url is present |
| 3 | `audit-staged-versus-committed` | tool | `tool/staged-vs-committed-load-auditor` | - |

