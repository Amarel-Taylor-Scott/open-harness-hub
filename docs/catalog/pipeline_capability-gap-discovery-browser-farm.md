# Capability gap discovery browser farm

*pipeline* · `pipeline/capability-gap-discovery-browser-farm` · v0.1.0 · experimental

Coordinate browser, search, and embedding agents to discover high-value LLM capability gaps and rank candidate primitives, pipelines, evals, and deployment blueprints.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | research, retrieval, evaluation, planning |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | external |
| freshness | volatile |
| license | MIT |



## Task

Find and rank areas where out-of-box LLMs are weak but reusable pipelines and primitives can create measurable capability lift.

**pipeline_kind:** `research_web.capability_gap_discovery`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_discovery_patterns` | knowledge_pack | `knowledge-pack/capability-gap-discovery-patterns` | - |
| 2 | `semantic_prior_search` | tool | `tool/embedding-index-search` | - |
| 3 | `source_router` | tool | `tool/search-provider-router` | - |
| 4 | `dataset_browser` | tool | `tool/browser-research-session` | - |
| 5 | `paper_browser` | tool | `tool/browser-research-session` | - |
| 6 | `red_team_browser` | tool | `tool/browser-research-session` | - |
| 7 | `normalize_findings` | tool | `tool/search-result-normalizer` | - |
| 8 | `score_findings` | tool | `tool/capability-gap-signal-scorer` | - |
| 9 | `audit` | processor | `processor/audit-trace-emitter` | - |

