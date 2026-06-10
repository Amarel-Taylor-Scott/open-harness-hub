# Daily promotion readiness audit

*pipeline* · `pipeline/daily-promotion-readiness-audit` · v0.1.0 · experimental

Audits a staged daily production run and routes rows by candidate-load readiness, review blockers, embedding execution blockers, and active promotion readiness.

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

Determine which staged daily component candidates are ready for candidate-table load and which remain blocked from active promotion.

**pipeline_kind:** `research_web.daily_promotion_readiness_audit`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-readiness-checks` | knowledge_pack | `knowledge-pack/daily-promotion-readiness-patterns` | - |
| 2 | `plan-promotion-readiness` | tool | `tool/daily-promotion-readiness-planner` | - |

