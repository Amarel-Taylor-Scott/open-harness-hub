# Index coverage repair

*pipeline* · `pipeline/index-coverage-repair` · v0.1.0 · experimental

Audits staged component candidate batches and emits missing hybrid-search index records before promotion readiness or database loading.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | retrieval, governance, verification, planning |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Find missing keyword, vector, graph, facet, or quality index records in staged component rows and produce repair JSONL without mutating a database.

**pipeline_kind:** `research_web.index_coverage_repair`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-index-coverage-patterns` | knowledge_pack | `knowledge-pack/index-coverage-repair-patterns` | - |
| 2 | `plan-index-coverage-repair` | tool | `tool/index-coverage-repair-planner` | - |
| 3 | `route-repair-output` | tool | `tool/object-factory-job-router` | - |

