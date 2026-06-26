---
name: multimodal-generation-blueprint
description: Generate a deployable multimodal media pipeline with provider routing,
  cost estimate, asset storage, safety screening, and provenance.
when_to_use: 'Pipeline kind: generate_media.multimodal_blueprint.'
---

# Multimodal generation blueprint

Plan, route, generate, store, safety-screen, and cost-estimate image, video, audio, music, document, or 3D generation workflows.

## Task

Generate a deployable multimodal media pipeline with provider routing, cost estimate, asset storage, safety screening, and provenance.

## Steps

1. **route_generation** — `tool` → `tool/generative-media-router`
2. **estimate_runtime_pricing** — `tool` → `tool/cloud-runtime-pricing-lookup`
3. **store_asset** — `tool` → `tool/multimodal-asset-store`
4. **screen_asset** — `tool` → `tool/multimodal-safety-screen`
5. **audit** — `processor` → `processor/audit-trace-emitter`

## Success criteria

- deterministic `$.outputs.generation_plan` is_truthy `True`
- deterministic `$.outputs.safety_report` is_truthy `True`

## Provenance

- Hub component: `pipeline/multimodal-generation-blueprint` v0.1.0
- License: `MIT`
- Industry: ai, media, cross_industry
- Full source manifest: see `references/manifest.yaml`
