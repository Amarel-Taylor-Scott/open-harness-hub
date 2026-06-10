# Promotion decision load plan

*pipeline* · `pipeline/promotion-decision-load-plan` · v0.1.0 · experimental

Creates CSV and SQL load bundles for promotion decisions, quality index rows, and review tickets so component candidates can move through a database-backed review gate.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | evaluation, governance, routing, verification |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Create a review-gated Postgres load plan for candidate promotion decisions, quality index rows, and review tickets.

**pipeline_kind:** `research_web.promotion_decision_load_plan`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-promotion-checks` | knowledge_pack | `knowledge-pack/promotion-decision-load-patterns` | - |
| 2 | `plan-promotion-decision-load` | tool | `tool/promotion-decision-load-planner` | - |
| 3 | `audit-staged-vs-committed` | tool | `tool/staged-vs-committed-load-auditor` | - |

