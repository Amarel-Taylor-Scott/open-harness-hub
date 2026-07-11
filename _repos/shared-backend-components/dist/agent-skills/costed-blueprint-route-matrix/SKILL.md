---
name: costed-blueprint-route-matrix
description: Build cheap, balanced, quality-first, and local-first blueprint options
  with guardrails, pricing snapshots, runtime estimates, and A/B cost-quality evaluation
  arms.
when_to_use: 'Pipeline kind: meta_build.costed_blueprint.'
---

# Costed blueprint route matrix

Composes model routing, active pricing, cloud runtime pricing, guardrails, and A/B test planning into comparable deployment options for a sentence-to-pipeline SaaS request.

## Task

Build cheap, balanced, quality-first, and local-first blueprint options with guardrails, pricing snapshots, runtime estimates, and A/B cost-quality evaluation arms.

## Steps

1. **route-models** — `tool` → `tool/model-capability-router`
2. **lookup-model-pricing** — `tool` → `tool/model-pricing-lookup`
3. **lookup-runtime-pricing** — `tool` → `tool/cloud-runtime-pricing-lookup`
4. **build-route-matrix** — `tool` → `tool/blueprint-route-matrix-builder`
5. **plan-cost-quality-ab** — `tool` → `tool/blueprint-ab-cost-quality-planner`
6. **emit-terraform-placeholder** — `tool` → `tool/terraform-blueprint-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/costed-blueprint-route-patterns`, `knowledge-pack/local-demo-verified-fact-patterns`

## Success criteria

- semantic must_cover ['cheap route', 'balanced route', 'quality-first route', 'pricing assumptions', 'guardrails', 'review queue'] against `$.route_matrix`
- deterministic `$.ab_plan` is_truthy `True`

## Provenance

- Hub component: `pipeline/costed-blueprint-route-matrix` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, government, finance, humanitarian, cross_industry
- Full source manifest: see `references/manifest.yaml`
