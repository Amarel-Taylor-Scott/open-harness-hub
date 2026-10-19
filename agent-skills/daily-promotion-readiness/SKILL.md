---
name: daily-promotion-readiness
description: Audit staged factory rows and produce promotion-readiness and review-queue
  evidence before database load or active publication.
when_to_use: 'Pipeline kind: research_web.daily_promotion_readiness.'
---

# Daily promotion readiness

Separates candidate-table load readiness from active component promotion readiness for high-volume daily production and model-ops component runs.

## Task

Audit staged factory rows and produce promotion-readiness and review-queue evidence before database load or active publication.

## Steps

1. **load-readiness-patterns** — `knowledge_pack` → `knowledge-pack/daily-promotion-readiness-patterns`
2. **plan-promotion-readiness** — `tool` → `tool/daily-promotion-readiness-planner`
3. **route-blocked-candidates** — `tool` → `tool/object-factory-job-router`

## Defaults

- **knowledge_packs**: `knowledge-pack/daily-promotion-readiness-patterns`

## Success criteria

- deterministic `$.daily_promotion_readiness_plan.counts.normalized_objects` > `0`
- deterministic `$.daily_promotion_readiness_plan.counts.active_promotion_ready` <= `$.daily_promotion_readiness_plan.counts.candidate_load_ready`
- semantic must_cover ['candidate-table load readiness', 'active component promotion readiness', 'review tickets', 'embedding execution', 'no Postgres side effects'] against `$.daily_promotion_readiness_plan`

## Provenance

- Hub component: `pipeline/daily-promotion-readiness` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
