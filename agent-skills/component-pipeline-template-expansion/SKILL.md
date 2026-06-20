---
name: component-pipeline-template-expansion
description: Expand a user task into an off-the-shelf pipeline template made from
  reusable components and control-flow steps.
when_to_use: 'Pipeline kind: component_pipeline_template_expansion.'
---

# Component pipeline template expansion

Turns a task sentence into a reusable component pipeline template with explicit pre-LLM, LLM, post-LLM, and control-flow stages.

## Task

Expand a user task into an off-the-shelf pipeline template made from reusable components and control-flow steps.

## Steps

1. **retrieve-layer-patterns** — `knowledge_pack` → `knowledge-pack/component-layer-control-flow-patterns`
2. **expand-template** — `tool` → `tool/component-pipeline-template-expander`
3. **check-sensitive-output** — `tool` → `tool/sensitive-data-object-gate`

## Defaults

- **knowledge_packs**: `knowledge-pack/component-layer-control-flow-patterns`

## Success criteria

- semantic must_cover ['pre_llm', 'llm', 'post_llm', 'control_flow', 'iterate'] against `$.component_pipeline_template`

## Provenance

- Hub component: `pipeline/component-pipeline-template-expansion` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
