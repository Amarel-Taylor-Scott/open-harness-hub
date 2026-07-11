# Vector readiness audit

*pipeline* · `pipeline/vector-readiness-audit` · v0.1.0 · experimental

Reconciles planned embedding completion rows with stored vector metadata so hybrid search indexes can distinguish planned, missing, ready, mismatched, and orphaned vectors.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | retrieval, embedding, governance, evaluation, verification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Audit vector search readiness by comparing embedding completion stubs with stored vector metadata.

**pipeline_kind:** `research_web.vector_readiness_audit`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-readiness-checks` | knowledge_pack | `knowledge-pack/vector-readiness-audit-patterns` | - |
| 2 | `audit-vector-readiness` | tool | `tool/vector-readiness-auditor` | - |
| 3 | `route-missing-or-mismatched-vectors` | tool | `tool/object-factory-job-router` | - |

