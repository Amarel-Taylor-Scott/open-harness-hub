---
name: multimodal-public-service-harness-intake
description: Convert public-service and quality use cases into reusable multimodal
  harness primitives and generated database rows.
when_to_use: 'Pipeline kind: agent_loop.'
---

# Multimodal public service harness intake

Normalizes disaster assistance, water quality, and food quality use cases into multi-model harnesses, generated row shards, source-governed facts, review tickets, and index records.

## Task

Convert public-service and quality use cases into reusable multimodal harness primitives and generated database rows.

## Steps

1. **source-governance** — `tool` → `tool/source-record-governance-router`
2. **route-evidence** — `tool` → `tool/multimodal-evidence-router`
3. **model-route** — `tool` → `tool/model-capability-router`
4. **disaster-assistance** — `harness` → `harness/disaster-assistance-multimodal-intake` (when `domain == humanitarian.disaster`)
5. **water-quality** — `harness` → `harness/water-quality-multimodal-triage` (when `domain == environmental.water`)
6. **food-quality** — `harness` → `harness/food-quality-multimodal-hold-release` (when `domain == food.safety`)
7. **safety-screen** — `tool` → `tool/multimodal-safety-screen`
8. **emit-index** — `tool` → `tool/index-record-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/multimodal-public-service-patterns`

## Success criteria

- semantic must_cover ['model routing', 'official-source retrieval', 'multimodal evidence normalization', 'human review routing', 'cost policy'] against `$.harness_blueprint`
- deterministic `$.model_route_plan` is_truthy `True`

## Provenance

- Hub component: `pipeline/multimodal-public-service-harness-intake` v0.1.0
- License: `MIT`
- Industry: humanitarian.disaster, government.benefits, environmental.water, water_utility.sdwa, food.safety, food_safety
- Full source manifest: see `references/manifest.yaml`
