# Approved promotion smoke test

*pipeline* · `pipeline/approved-promotion-smoke-test` · v0.1.0 · experimental

Runs a synthetic approved candidate through active component promotion, component versioning, CDC, index projection, and review-ticket routing.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, verification, evaluation, retrieval |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Prove that an approved component candidate can flow through active component publication, component versioning, CDC rows, index projection, and review routing.

**pipeline_kind:** `research_web.approved_promotion_smoke_test`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-smoke-checks` | knowledge_pack | `knowledge-pack/approved-promotion-smoke-patterns` | - |
| 2 | `run-approved-promotion-smoke` | tool | `tool/approved-promotion-smoke-planner` | - |

