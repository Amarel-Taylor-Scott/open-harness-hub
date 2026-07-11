# Promotion CDC bridge plan

*pipeline* · `pipeline/promotion-cdc-bridge-plan` · v0.1.0 · experimental

Turns approved component promotion outputs into immutable component change events plus freshness, graph, and review records for database-first lifecycle management.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, verification, retrieval, evaluation |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Bridge review-approved component publication into CDC rows so component versions, search indexes, and review queues remain incremental and auditable.

**pipeline_kind:** `research_web.promotion_cdc_bridge_plan`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-promotion-cdc-bridge-checks` | knowledge_pack | `knowledge-pack/promotion-cdc-bridge-patterns` | - |
| 2 | `bridge-promotion-to-cdc` | tool | `tool/promotion-cdc-bridge-planner` | - |
| 3 | `audit-staged-vs-committed` | tool | `tool/staged-vs-committed-load-auditor` | - |

