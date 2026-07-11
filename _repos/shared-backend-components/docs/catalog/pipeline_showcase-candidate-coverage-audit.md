# Showcase candidate coverage audit

*pipeline* · `pipeline/showcase-candidate-coverage-audit` · v0.1.0 · experimental

Compares daily showcase pipeline templates with staged component candidates and emits missing-component generation requests for weak template steps.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | planning, retrieval, evaluation, governance |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Audit whether generated showcase pipelines have enough staged component candidates to become credible off-the-shelf product templates.

**pipeline_kind:** `research_web.showcase_candidate_coverage_audit`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-coverage-checks` | knowledge_pack | `knowledge-pack/showcase-candidate-coverage-patterns` | - |
| 2 | `score-showcase-coverage` | tool | `tool/showcase-candidate-coverage-reporter` | - |

