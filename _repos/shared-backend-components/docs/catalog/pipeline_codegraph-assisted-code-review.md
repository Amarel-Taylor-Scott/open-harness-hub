# CodeGraph-assisted code review (DevOps)

*pipeline* · `pipeline/codegraph-assisted-code-review` · v0.1.0 · experimental

Seed pipeline for the DevOps section. Given the changed symbols in a pull
request, pull their dependents from a local code knowledge graph (so the
reviewer/agent sees blast radius without reading the whole repo), then persist
that review context to durable memory keyed by the PR so it survives across
commits and sessions.

Composes two catalogued open-source tools — tool/codegraph-code-graph-query
and tool/agentmemory-persistent-memory — and is intentionally minimal: extend
it with a review harness (LLM risk summary) and a rubric/benchmark. Token-
efficient by construction (pairs with pattern/input-token-compression and
pattern/twelve-factor-agent).

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | retrieval, memory, governance |
| modality | code, text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

From the changed symbols in a pull request, retrieve their dependents from a local code graph and persist the review context to durable memory keyed by the PR.

**pipeline_kind:** `devops.code_review_assist`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `retrieve-impacted-symbols` | tool | `tool/codegraph-code-graph-query` | - |
| 2 | `persist-review-context` | tool | `tool/agentmemory-persistent-memory` | - |

