---
name: approved-component-promotion-plan
description: Create a review-gated Postgres load plan for active components, versions,
  subcomponents, and candidate state transitions.
when_to_use: 'Pipeline kind: research_web.approved_component_promotion_plan.'
---

# Approved component promotion plan

Creates CSV and SQL load bundles that move only review-approved component candidates into active Postgres component, component version, and subcomponent rows.

## Task

Create a review-gated Postgres load plan for active components, versions, subcomponents, and candidate state transitions.

## Steps

1. **load-approved-promotion-checks** — `knowledge_pack` → `knowledge-pack/approved-component-promotion-patterns`
2. **plan-approved-component-promotion** — `tool` → `tool/approved-component-promotion-planner`
3. **audit-staged-vs-committed** — `tool` → `tool/staged-vs-committed-load-auditor`

## Defaults

- **knowledge_packs**: `knowledge-pack/approved-component-promotion-patterns`

## Success criteria

- deterministic `$.approved_component_promotion_plan.candidate_state_update_count` > `0`
- deterministic `$.approved_component_promotion_plan.approved_component_count` >= `0`
- semantic must_cover ['review-approved candidates', 'active component rows', 'component versions', 'subcomponents', 'candidate state transitions'] against `$.approved_component_promotion_plan`

## Provenance

- Hub component: `pipeline/approved-component-promotion-plan` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
