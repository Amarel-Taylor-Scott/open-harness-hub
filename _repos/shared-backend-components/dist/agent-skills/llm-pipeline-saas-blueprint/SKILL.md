---
name: llm-pipeline-saas-blueprint
description: Generate costed LLM pipeline options and deployable blueprints from a
  user's natural-language task, hosting constraints, and budget.
when_to_use: 'Pipeline kind: meta_build.costed_blueprint.'
---

# LLM pipeline SaaS blueprint generator

Convert a free-text LLM task request into costed pipeline options, retrieval/runtime tool choices, deployment blueprints, Terraform/runtime skeletons, evaluation components, and MCP setup plans.

## Task

Generate costed LLM pipeline options and deployable blueprints from a user's natural-language task, hosting constraints, and budget.

## Steps

1. **catalog_recommendation** — `pipeline` → `pipeline/recommend-pipeline-from-prompt`
2. **model_pricing** — `tool` → `tool/model-pricing-lookup`
3. **semantic_catalog_search** — `tool` → `tool/embedding-index-search`
4. **search_provider_selection** — `tool` → `tool/search-provider-router` (when `$.inputs.discovery_preferences.allow_search == true`)
5. **fresh_web_search** — `tool` → `tool/web-search` (when `$.inputs.discovery_preferences.allow_public_web == true`)
6. **custom_cloud_search** — `tool` → `tool/cloud-search-function-adapter` (when `$.steps.search_provider_selection.output.provider_kind == 'cloud_function'`)
7. **containerized_search_runtime** — `tool` → `tool/containerized-search-runtime` (when `$.steps.search_provider_selection.output.provider_kind == 'container'`)
8. **search_normalization** — `tool` → `tool/search-result-normalizer` (when `$.inputs.discovery_preferences.allow_search == true`)
9. **browser_research** — `tool` → `tool/browser-research-session` (when `$.inputs.discovery_preferences.requires_rendered_pages == true`)
10. **browser_local_llm_profile** — `tool` → `tool/browser-local-llm-runner` (when `$.inputs.discovery_preferences.allow_browser_local_runtime == true`)
11. **runtime_pricing** — `tool` → `tool/cloud-runtime-pricing-lookup`
12. **cost_gate** — `processor` → `processor/cost-ceiling-gate`
13. **terraform_blueprint** — `tool` → `tool/terraform-blueprint-emitter`
14. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/llm-pipeline-saas-blueprints`, `knowledge-pack/pipeline-generation-scenarios`
- **rule_packs**: `rule-pack/hybrid-retrieval-policy`

## Success criteria

- deterministic `$.outputs.options` is_truthy `True`
- deterministic `$.outputs.cost_estimate` is_truthy `True`

## Provenance

- Hub component: `pipeline/llm-pipeline-saas-blueprint` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
