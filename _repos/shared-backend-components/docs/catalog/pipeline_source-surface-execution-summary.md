# Source surface execution summary

*pipeline* · `pipeline/source-surface-execution-summary` · v0.1.0 · experimental

Aggregates source-surface factory run progress across partitions, jobs, replay records, generated rows, promotion decisions, review tickets, and load readiness.

| axis | value |
|---|---|
| industry | government, software, media, construction, energy, finance, healthcare, cross_industry |
| capability | governance, evaluation, retrieval, routing, serving |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Report source-surface object-factory progress and load readiness without confusing generated row counts with curated YAML manifest counts.

**pipeline_kind:** `research_web.source_surface_execution_summary`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-summary-inputs` | tool | `tool/source-record-governance-router` | - |
| 2 | `summarize-source-surface-execution` | tool | `tool/source-surface-execution-summary-reporter` | - |
| 3 | `route-review-attention` | tool | `tool/object-factory-job-router` | - |

