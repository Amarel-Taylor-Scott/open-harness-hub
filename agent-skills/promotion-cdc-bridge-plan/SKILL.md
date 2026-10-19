---
name: promotion-cdc-bridge-plan
description: Bridge review-approved component publication into CDC rows so component
  versions, search indexes, and review queues remain incremental and auditable.
when_to_use: 'Pipeline kind: research_web.promotion_cdc_bridge_plan.'
---

# Promotion CDC bridge plan

Turns approved component promotion outputs into immutable component change events plus freshness, graph, and review records for database-first lifecycle management.

## Task

Bridge review-approved component publication into CDC rows so component versions, search indexes, and review queues remain incremental and auditable.

## Steps

1. **load-promotion-cdc-bridge-checks** — `knowledge_pack` → `knowledge-pack/promotion-cdc-bridge-patterns`
2. **bridge-promotion-to-cdc** — `tool` → `tool/promotion-cdc-bridge-planner`
3. **audit-staged-vs-committed** — `tool` → `tool/staged-vs-committed-load-auditor`

## Defaults

- **knowledge_packs**: `knowledge-pack/promotion-cdc-bridge-patterns`

## Success criteria

- deterministic `$.promotion_cdc_bridge_plan.cdc.change_event_count` >= `0`
- semantic must_cover ['component versions', 'change events', 'index records', 'review tickets', 'load SQL'] against `$.promotion_cdc_bridge_plan`

## Provenance

- Hub component: `pipeline/promotion-cdc-bridge-plan` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
