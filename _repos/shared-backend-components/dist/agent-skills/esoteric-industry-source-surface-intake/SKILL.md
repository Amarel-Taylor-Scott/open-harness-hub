---
name: esoteric-industry-source-surface-intake
description: Turn esoteric industry source-surface seeds into governed candidate primitive
  plans with flexible labels and review routing.
when_to_use: 'Pipeline kind: research_web.esoteric_industry_source_surface_intake.'
---

# Esoteric industry source surface intake

Normalizes esoteric vertical source-surface seeds for automotive, employment agencies, plumbing and HVAC, woodworking, offshore oil and gas, and environmental reviews into candidate primitive plans.

## Task

Turn esoteric industry source-surface seeds into governed candidate primitive plans with flexible labels and review routing.

## Steps

1. **govern-source-surface-seeds** — `tool` → `tool/source-record-governance-router`
2. **normalize-source-surfaces** — `tool` → `tool/esoteric-source-surface-normalizer`
3. **emit-candidate-index** — `tool` → `tool/index-record-emitter`
4. **export-factory-rows** — `tool` → `tool/source-surface-seed-row-exporter`

## Defaults

- **knowledge_packs**: `knowledge-pack/esoteric-industry-source-surfaces`, `knowledge-pack/source-surface-seed-row-patterns`, `knowledge-pack/flexible-hierarchy-label-patterns`

## Success criteria

- semantic must_cover ['automotive sales', 'employment agency fee rules', 'plumbing HVAC permits', 'woodworking shop workflow', 'offshore oil and gas', 'environmental review'] against `$.candidate_primitives`

## Provenance

- Hub component: `pipeline/esoteric-industry-source-surface-intake` v0.1.0
- License: `MIT`
- Industry: automotive, energy, manufacturing, construction, government, cross_industry
- Full source manifest: see `references/manifest.yaml`
