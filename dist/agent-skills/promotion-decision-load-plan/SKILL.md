---
name: promotion-decision-load-plan
description: Create a review-gated Postgres load plan for candidate promotion decisions,
  quality index rows, and review tickets.
when_to_use: 'Pipeline kind: research_web.promotion_decision_load_plan.'
---

# Promotion decision load plan

Creates CSV and SQL load bundles for promotion decisions, quality index rows, and review tickets so component candidates can move through a database-backed review gate.

## Task

Create a review-gated Postgres load plan for candidate promotion decisions, quality index rows, and review tickets.

## Steps

1. **load-promotion-checks** — `knowledge_pack` → `knowledge-pack/promotion-decision-load-patterns`
2. **plan-promotion-decision-load** — `tool` → `tool/promotion-decision-load-planner`
3. **audit-staged-vs-committed** — `tool` → `tool/staged-vs-committed-load-auditor`

## Defaults

- **knowledge_packs**: `knowledge-pack/promotion-decision-load-patterns`

## Success criteria

- deterministic `$.promotion_decision_load_plan.promotion_decision_count` > `0`
- deterministic `$.promotion_decision_load_plan.index_record_count` > `0`
- semantic must_cover ['promotion decisions', 'quality index records', 'review tickets', 'review gated promotion'] against `$.promotion_decision_load_plan`

## Provenance

- Hub component: `pipeline/promotion-decision-load-plan` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
