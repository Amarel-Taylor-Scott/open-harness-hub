---
name: showcase-gaps-to-component-candidates
description: Convert showcase coverage gaps into targeted candidate components so
  the daily pipeline demos improve automatically over time.
when_to_use: 'Pipeline kind: research_web.showcase_gaps_to_component_candidates.'
---

# Showcase gaps to component candidates

Feeds partial or missing showcase template coverage requests back into the component factory as targeted database-backed candidate rows.

## Task

Convert showcase coverage gaps into targeted candidate components so the daily pipeline demos improve automatically over time.

## Steps

1. **load-gap-generation-checks** — `knowledge_pack` → `knowledge-pack/showcase-gap-component-patterns`
2. **generate-gap-component-rows** — `tool` → `tool/showcase-gap-component-seed-generator`

## Defaults

- **knowledge_packs**: `knowledge-pack/showcase-gap-component-patterns`, `knowledge-pack/showcase-candidate-coverage-patterns`

## Success criteria

- deterministic `$.generate-gap-component-rows.seed_count` >= `1`
- deterministic `$.generate-gap-component-rows.row_counts.index_record` >= `5`
- semantic must_cover ['showcase coverage', 'targeted component candidate', 'review-gated', 'database-backed'] against `$.generate-gap-component-rows`

## Provenance

- Hub component: `pipeline/showcase-gaps-to-component-candidates` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
