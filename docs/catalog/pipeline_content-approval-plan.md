# Content approval plan

*pipeline* · `pipeline/content-approval-plan` · v0.1.0 · experimental

Creates CSV, JSONL, and SQL load bundles that approve or route dedupe-resolved component candidates before active promotion.

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

Create a review-gated Postgres load plan for content approval decisions and derived promotion decisions.

**pipeline_kind:** `research_web.content_approval_plan`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-content-approval-checks` | knowledge_pack | `knowledge-pack/content-approval-patterns` | - |
| 2 | `plan-content-approval` | tool | `tool/content-approval-planner` | - |
| 3 | `audit-staged-vs-committed` | tool | `tool/staged-vs-committed-load-auditor` | - |

