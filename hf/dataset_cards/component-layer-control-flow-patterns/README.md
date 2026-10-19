---
license: CC-BY-4.0
tags:
- ai
- components
- control-flow
- cross_industry
- experimental
- llm
- open-harness-hub
- pipeline-templates
- planning
- post-llm
- pre-llm
- routing
- serving
- software.devops
- subcomponents
- verification
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Component layer and control-flow patterns
---

# Component layer and control-flow patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/component-layer-control-flow-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Reusable layer labels and orchestration controls for composing pre-LLM, LLM, post-LLM, and control-flow components into off-the-shelf pipelines.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: planning, routing, serving, verification
**Modalities**: structured, text, image, audio, video
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `component_layer_pattern`
- `control_flow_pattern`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/component-layer-control-flow-patterns/patterns.jsonl` | jsonl | component_layer_control_flow_pattern |

## Provenance

- **sources**: Open Harness Hub Postgres schema, Open Harness Hub pipeline runner schema
- **collected_through**: 2026-05-26
- **collected_by**: Open Harness Hub contributors
- **anonymization**: component labels only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/component-layer-control-flow-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{component-layer-control-flow-patterns_open_harness_hub,
  title  = {Component layer and control-flow patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/component-layer-control-flow-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/component-layer-control-flow-patterns`.
