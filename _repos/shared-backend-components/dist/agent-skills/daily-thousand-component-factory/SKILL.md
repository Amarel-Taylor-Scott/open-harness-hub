---
name: daily-thousand-component-factory
description: Create a daily-scale batch of database-backed component candidates that
  can be searched, filtered, customized, reviewed, promoted, and wired into pipeline
  templates.
when_to_use: 'Pipeline kind: research_web.daily_thousand_component_factory.'
---

# Daily thousand component factory

Generates 1,000 searchable, label-rich, database-backed component candidates per run, ready for dedupe, approval, promotion, and CDC gates.

## Task

Create a daily-scale batch of database-backed component candidates that can be searched, filtered, customized, reviewed, promoted, and wired into pipeline templates.

## Steps

1. **load-daily-factory-checks** — `knowledge_pack` → `knowledge-pack/daily-thousand-component-factory-patterns`
2. **generate-daily-component-candidates** — `tool` → `tool/daily-thousand-component-seed-generator`
3. **bulk-load-ready-rows** — `tool` → `tool/factory-jsonl-bulk-copy-loader`

## Defaults

- **knowledge_packs**: `knowledge-pack/daily-thousand-component-factory-patterns`

## Success criteria

- deterministic `$.generate-daily-component-candidates.seed_count` >= `1000`
- deterministic `$.generate-daily-component-candidates.row_counts.index_record` >= `5000`
- semantic must_cover ['database-backed', 'searchable', 'customizable', 'review-gated', 'not one YAML file per component', 'named source-surface matrix'] against `$.generate-daily-component-candidates`

## Provenance

- Hub component: `pipeline/daily-thousand-component-factory` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
