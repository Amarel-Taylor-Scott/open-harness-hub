---
license: CC-BY-4.0
tags:
- ai
- compliance
- cost-aware
- evaluation
- experimental
- humanitarian
- media
- moderation
- open-harness-hub
- pipeline-generation
- planning
- routing
- scenario-tests
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Cost-aware pipeline generation scenarios
---

# Cost-aware pipeline generation scenarios

<!-- Generated from OpenHubForAI manifest `knowledge-pack/pipeline-generation-scenarios` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Synthetic scenario prompts and expected planning constraints for generating safe, cost-bounded moderation and review pipelines.

**Industries**: ai, media, compliance, humanitarian
**Capabilities**: planning, evaluation, routing
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `scenario_prompt`
- `expected_pipeline_constraints`
- `cost_band`

## Files

| path | format | schema |
|---|---|---|
| `data/pipeline-generation-scenarios/scenario-prompts.jsonl` | jsonl | — |

## Provenance

- **sources**: OpenHubForAI synthetic scenario design
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: fully synthetic; no real users, workers, children, or platform posts

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/pipeline-generation-scenarios.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{pipeline-generation-scenarios_open_harness_hub,
  title  = {Cost-aware pipeline generation scenarios},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/pipeline-generation-scenarios},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/pipeline-generation-scenarios`.
