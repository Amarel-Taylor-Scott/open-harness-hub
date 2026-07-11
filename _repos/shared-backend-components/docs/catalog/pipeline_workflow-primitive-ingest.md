# Workflow primitive ingest

*pipeline* · `pipeline/workflow-primitive-ingest` · v0.1.0 · experimental

Import AI workflow graphs from systems such as ComfyUI, n8n, Flowise, Dify, and Langflow, then normalize, safety-scan, score, and index reusable primitives.

| axis | value |
|---|---|
| industry | ai, software.devops, media, cross_industry |
| capability | retrieval, format_conversion, evaluation, governance |
| modality | text, image, video, audio, music, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Convert external AI workflow graphs into searchable candidate primitives with safety, cost, provenance, and evaluation metadata.

**pipeline_kind:** `research_web.workflow_primitive_ingest`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `normalize_workflow` | tool | `tool/workflow-import-normalizer` | - |
| 2 | `scan_nodes` | tool | `tool/workflow-node-safety-scanner` | - |
| 3 | `score_primitives` | tool | `tool/capability-gap-signal-scorer` | - |
| 4 | `plan_index` | tool | `tool/primitive-index-orchestrator` | - |
| 5 | `audit` | processor | `processor/audit-trace-emitter` | - |

