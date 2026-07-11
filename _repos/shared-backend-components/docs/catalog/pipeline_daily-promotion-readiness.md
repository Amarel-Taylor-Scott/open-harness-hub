# Daily promotion readiness

*pipeline* · `pipeline/daily-promotion-readiness` · v0.1.0 · experimental

Separates candidate-table load readiness from active component promotion readiness for high-volume daily production and model-ops component runs.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, evaluation, retrieval, planning |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Audit staged factory rows and produce promotion-readiness and review-queue evidence before database load or active publication.

**pipeline_kind:** `research_web.daily_promotion_readiness`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-readiness-patterns` | knowledge_pack | `knowledge-pack/daily-promotion-readiness-patterns` | - |
| 2 | `plan-promotion-readiness` | tool | `tool/daily-promotion-readiness-planner` | - |
| 3 | `route-blocked-candidates` | tool | `tool/object-factory-job-router` | - |

