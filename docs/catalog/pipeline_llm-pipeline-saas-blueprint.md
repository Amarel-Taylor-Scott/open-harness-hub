# LLM pipeline SaaS blueprint generator

*pipeline* · `pipeline/llm-pipeline-saas-blueprint` · v0.1.0 · experimental

Convert a free-text LLM task request into costed pipeline options, retrieval/runtime tool choices, deployment blueprints, Terraform/runtime skeletons, evaluation components, and MCP setup plans.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | planning, generation, evaluation, tool_use |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Generate costed LLM pipeline options and deployable blueprints from a user's natural-language task, hosting constraints, and budget.

**pipeline_kind:** `meta_build.costed_blueprint`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `catalog_recommendation` | pipeline | `pipeline/recommend-pipeline-from-prompt` | - |
| 2 | `model_pricing` | tool | `tool/model-pricing-lookup` | - |
| 3 | `semantic_catalog_search` | tool | `tool/embedding-index-search` | - |
| 4 | `search_provider_selection` | tool | `tool/search-provider-router` | $.inputs.discovery_preferences.allow_search == true |
| 5 | `fresh_web_search` | tool | `tool/web-search` | $.inputs.discovery_preferences.allow_public_web == true |
| 6 | `custom_cloud_search` | tool | `tool/cloud-search-function-adapter` | $.steps.search_provider_selection.output.provider_kind == 'cloud_function' |
| 7 | `containerized_search_runtime` | tool | `tool/containerized-search-runtime` | $.steps.search_provider_selection.output.provider_kind == 'container' |
| 8 | `search_normalization` | tool | `tool/search-result-normalizer` | $.inputs.discovery_preferences.allow_search == true |
| 9 | `browser_research` | tool | `tool/browser-research-session` | $.inputs.discovery_preferences.requires_rendered_pages == true |
| 10 | `browser_local_llm_profile` | tool | `tool/browser-local-llm-runner` | $.inputs.discovery_preferences.allow_browser_local_runtime == true |
| 11 | `runtime_pricing` | tool | `tool/cloud-runtime-pricing-lookup` | - |
| 12 | `cost_gate` | processor | `processor/cost-ceiling-gate` | - |
| 13 | `terraform_blueprint` | tool | `tool/terraform-blueprint-emitter` | - |
| 14 | `audit` | processor | `processor/audit-trace-emitter` | - |

