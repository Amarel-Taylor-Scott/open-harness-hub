---
name: component-store-candidate-load-plan
description: Create a review-gated Postgres load plan for generated component and
  subcomponent candidates.
when_to_use: 'Pipeline kind: research_web.component_store_candidate_load_plan.'
---

# Component store candidate load plan

Creates CSV and SQL load bundles that place generated components and subcomponents into Postgres candidate tables while preserving review gates and source provenance.

## Task

Create a review-gated Postgres load plan for generated component and subcomponent candidates.

## Steps

1. **load-component-store-checks** — `knowledge_pack` → `knowledge-pack/component-store-load-patterns`
2. **plan-component-store-load** — `tool` → `tool/component-store-load-planner`
3. **audit-staged-vs-committed** — `tool` → `tool/staged-vs-committed-load-auditor`

## Defaults

- **knowledge_packs**: `knowledge-pack/component-store-load-patterns`

## Success criteria

- deterministic `$.component_store_load_plan.component_candidate_count` > `0`
- deterministic `$.component_store_load_plan.subcomponent_candidate_count` > `$.component_store_load_plan.component_candidate_count`
- semantic must_cover ['candidate tables', 'review gated promotion', 'source provenance', 'side effect free load plan'] against `$.component_store_load_plan`

## Provenance

- Hub component: `pipeline/component-store-candidate-load-plan` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
