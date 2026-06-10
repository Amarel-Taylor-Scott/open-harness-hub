# Component pipeline template expansion

*pipeline* · `pipeline/component-pipeline-template-expansion` · v0.1.0 · experimental

Turns a task sentence into a reusable component pipeline template with explicit pre-LLM, LLM, post-LLM, and control-flow stages.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | planning, routing, serving, verification |
| modality | structured, text, image, audio, video |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Expand a user task into an off-the-shelf pipeline template made from reusable components and control-flow steps.

**pipeline_kind:** `component_pipeline_template_expansion`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `retrieve-layer-patterns` | knowledge_pack | `knowledge-pack/component-layer-control-flow-patterns` | - |
| 2 | `expand-template` | tool | `tool/component-pipeline-template-expander` | - |
| 3 | `check-sensitive-output` | tool | `tool/sensitive-data-object-gate` | - |

