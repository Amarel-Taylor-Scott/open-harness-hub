---
name: daily-showcase-pipeline-factory
description: Generate daily off-the-shelf pipeline templates that prove how database-backed
  component candidates become usable product workflows.
when_to_use: 'Pipeline kind: research_web.daily_showcase_pipeline_factory.'
---

# Daily showcase pipeline factory

Creates 5 to 25 preconfigured, review-ready showcase pipeline templates per day and prepares them for Postgres component-template loading.

## Task

Generate daily off-the-shelf pipeline templates that prove how database-backed component candidates become usable product workflows.

## Steps

1. **load-showcase-scenarios** — `knowledge_pack` → `knowledge-pack/daily-showcase-pipeline-patterns`
2. **generate-showcase-templates** — `tool` → `tool/daily-showcase-pipeline-generator`
3. **load-plan-review** — `tool` → `tool/component-template-load-planner`

## Defaults

- **knowledge_packs**: `knowledge-pack/daily-showcase-pipeline-patterns`, `knowledge-pack/component-template-load-patterns`

## Success criteria

- deterministic `$.generate-showcase-templates.showcase_template_count` >= `5`
- deterministic `$.generate-showcase-templates.showcase_template_count` <= `25`
- semantic must_cover ['pre-LLM', 'LLM', 'post-LLM', 'review gate', 'cost profile', 'deployment target'] against `$.generate-showcase-templates`

## Provenance

- Hub component: `pipeline/daily-showcase-pipeline-factory` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
