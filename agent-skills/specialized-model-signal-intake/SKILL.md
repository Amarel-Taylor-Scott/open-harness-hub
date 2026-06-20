---
name: specialized-model-signal-intake
description: Turn public task-specific model context into reusable knowledge objects,
  eval seeds, label schemas, model replacement routes, and review tickets.
when_to_use: 'Pipeline kind: research_web.specialized_model_signal_intake.'
---

# Specialized model signal intake

Mines task-specific model cards, model organizations, datasets, and leaderboards into governed candidate knowledge objects and pipeline primitives.

## Task

Turn public task-specific model context into reusable knowledge objects, eval seeds, label schemas, model replacement routes, and review tickets.

## Steps

1. **govern-model-sources** — `tool` → `tool/source-record-governance-router`
2. **normalize-model-cards** — `tool` → `tool/specialized-model-card-normalizer`
3. **link-model-signal-entities** — `tool` → `tool/entity-recognition-linker`
4. **dedupe-model-signal-primitives** — `tool` → `tool/fuzzy-dedupe-clusterer`
5. **emit-model-signal-index-records** — `tool` → `tool/index-record-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/specialized-model-signal-surfaces`

## Success criteria

- semantic must_cover ['task definition', 'label schema', 'training context', 'evaluation harness', 'model replacement route'] against `$.candidate_primitives`

## Provenance

- Hub component: `pipeline/specialized-model-signal-intake` v0.1.0
- License: `MIT`
- Industry: healthcare, finance, legal, software.devops, media, security, privacy, government, cross_industry
- Full source manifest: see `references/manifest.yaml`
