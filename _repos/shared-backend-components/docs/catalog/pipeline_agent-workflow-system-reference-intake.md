# Agent workflow system reference intake

*pipeline* · `pipeline/agent-workflow-system-reference-intake` · v0.1.0 · experimental

Safely plan reference intake for agent frameworks, skill marketplaces, and workflow systems, then extract normalized skill/workflow primitives without republishing upstream source files.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | retrieval, extraction, governance, safety, planning |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Study agent/workflow ecosystems through safe reference intake, extract reusable workflow and skill primitives, and route them through governance, labels, dedupe, and index emission.

**pipeline_kind:** `research_web.agent_workflow_reference_intake`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_agent_systems` | knowledge_pack | `knowledge-pack/agent-workflow-system-source-map` | - |
| 2 | `plan_reference_intake` | tool | `tool/reference-repo-intake-planner` | - |
| 3 | `extract_skill_workflows` | tool | `tool/skill-workflow-manifest-extractor` | - |
| 4 | `label_and_dimension` | pipeline | `pipeline/hybrid-label-vector-index` | - |
| 5 | `governance_entity_dedupe_index` | pipeline | `pipeline/source-governance-entity-dedupe-index` | - |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | - |

