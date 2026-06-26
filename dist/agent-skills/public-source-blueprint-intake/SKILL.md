---
name: public-source-blueprint-intake
description: Create governed public-source scan and normalization jobs for source
  families that can generate candidate primitives at scale.
when_to_use: 'Pipeline kind: research_web.public_source_blueprint_intake.'
---

# Public source blueprint intake

Turns public source blueprints for esoteric verticals into governed scan, archive, conversion, extraction, entity-linking, dedupe, indexing, and review plans.

## Task

Create governed public-source scan and normalization jobs for source families that can generate candidate primitives at scale.

## Steps

1. **govern-public-source-blueprints** — `tool` → `tool/source-record-governance-router`
2. **normalize-blueprints** — `tool` → `tool/public-source-blueprint-normalizer`
3. **scan-source-surface** — `tool` → `tool/primitive-source-surface-scanner`
4. **capture-archive** — `tool` → `tool/web-archive-capture-lookup`
5. **convert-page** — `tool` → `tool/page-to-markdown-converter`
6. **extract-normalized-objects** — `tool` → `tool/normalized-object-extractor`
7. **link-entities** — `tool` → `tool/entity-recognition-linker`
8. **dedupe-objects** — `tool` → `tool/fuzzy-dedupe-clusterer`
9. **emit-index-records** — `tool` → `tool/index-record-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/public-source-blueprint-catalog`, `knowledge-pack/esoteric-industry-source-surfaces`

## Success criteria

- semantic must_cover ['source governance', 'archive capture', 'page to markdown', 'entity linking', 'fuzzy dedupe', 'index record emission'] against `$.scan_jobs`

## Provenance

- Hub component: `pipeline/public-source-blueprint-intake` v0.1.0
- License: `MIT`
- Industry: automotive, energy, manufacturing, construction, government, cross_industry
- Full source manifest: see `references/manifest.yaml`
