# Local sentence-to-pipeline demo

*pipeline* · `pipeline/local-sentence-to-pipeline-demo` · v0.1.0 · experimental

Runs the downloadable local demo path: turn a plain-language request into costed LLM pipeline options with guardrails, eval kits, A/B cost-quality testing, and deployment bundle placeholders.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | planning, generation, evaluation, governance |
| modality | text, image, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



## Task

Convert a user sentence into cheap, balanced, and quality-first pipeline blueprints with guardrail and eval registry recommendations.

**pipeline_kind:** `meta_build.local_blueprint_demo`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `run-local-blueprint` | tool | `tool/sentence-to-pipeline-blueprint-runner` | - |
| 2 | `recommend-full-blueprint` | pipeline | `pipeline/llm-pipeline-saas-blueprint` | - |
| 3 | `screen-multimodal-safety` | tool | `tool/multimodal-safety-screen` | - |
| 4 | `cost-ab-test` | processor | `processor/cost-ceiling-gate` | - |

