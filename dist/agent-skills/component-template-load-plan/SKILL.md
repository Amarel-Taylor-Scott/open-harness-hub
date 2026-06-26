---
name: component-template-load-plan
description: Create a review-gated Postgres load plan for reusable component pipeline
  templates and ordered template steps.
when_to_use: 'Pipeline kind: research_web.component_template_load_plan.'
---

# Component template load plan

Creates CSV and SQL load bundles that place off-the-shelf component pipeline templates into Postgres template tables with ordered layer-aware steps.

## Task

Create a review-gated Postgres load plan for reusable component pipeline templates and ordered template steps.

## Steps

1. **load-template-checks** — `knowledge_pack` → `knowledge-pack/component-template-load-patterns`
2. **plan-template-load** — `tool` → `tool/component-template-load-planner`
3. **audit-staged-vs-committed** — `tool` → `tool/staged-vs-committed-load-auditor`

## Defaults

- **knowledge_packs**: `knowledge-pack/component-template-load-patterns`

## Success criteria

- deterministic `$.component_template_load_plan.template_count` > `0`
- deterministic `$.component_template_load_plan.template_step_count` > `0`
- semantic must_cover ['component pipeline template', 'ordered template steps', 'pre_llm', 'llm', 'post_llm', 'control_flow'] against `$.component_template_load_plan`

## Provenance

- Hub component: `pipeline/component-template-load-plan` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
