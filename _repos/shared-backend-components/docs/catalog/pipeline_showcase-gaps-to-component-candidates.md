# Showcase gaps to component candidates

*pipeline* · `pipeline/showcase-gaps-to-component-candidates` · v0.1.0 · experimental

Feeds partial or missing showcase template coverage requests back into the component factory as targeted database-backed candidate rows.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | generation, planning, retrieval, governance |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Convert showcase coverage gaps into targeted candidate components so the daily pipeline demos improve automatically over time.

**pipeline_kind:** `research_web.showcase_gaps_to_component_candidates`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-gap-generation-checks` | knowledge_pack | `knowledge-pack/showcase-gap-component-patterns` | - |
| 2 | `generate-gap-component-rows` | tool | `tool/showcase-gap-component-seed-generator` | - |

