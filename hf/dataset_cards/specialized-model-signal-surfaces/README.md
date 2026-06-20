---
license: CC-BY-4.0
tags:
- classification
- cross_industry
- embedding
- evaluation
- experimental
- extraction
- finance
- fine-tuning
- governance
- government
- healthcare
- huggingface
- knowledge-objects
- legal
- media
- model-cards
- open-harness-hub
- privacy
- retrieval
- routing
- security
- software.devops
- specialized-models
task_categories:
- sentence-similarity
- text-classification
- text-retrieval
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Specialized model signal surfaces
---

# Specialized model signal surfaces

<!-- Generated from Open Harness Hub manifest `knowledge-pack/specialized-model-signal-surfaces` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Research-backed seed objects for mining task-specific model cards, fine-tunes, leaderboards, and domain model repositories into reusable knowledge objects and pipeline primitives.

**Industries**: healthcare, finance, legal, software.devops, media, security, privacy, government, cross_industry
**Capabilities**: classification, extraction, retrieval, evaluation, routing, governance, embedding
**Modalities**: text, image, structured
**Freshness**: volatile
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `source_surface`
- `candidate_primitive`
- `task_definition`
- `label_schema`
- `evaluation_seed`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/specialized-model-signal-surfaces/models.jsonl` | jsonl | — |

## Provenance

- **sources**: https://huggingface.co/docs/hub/model-cards, https://huggingface.co/docs/hub/models-tasks, https://huggingface.co/OpenMed, https://huggingface.co/google/medgemma-4b-pt, https://huggingface.co/ProsusAI/finbert, https://huggingface.co/nlpaueb/legal-bert-base-uncased, https://huggingface.co/microsoft/codebert-base, https://huggingface.co/docs/transformers/v4.43.0/en/model_doc/layoutlm
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: public model metadata only; no private training data copied

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/specialized-model-signal-surfaces.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{specialized-model-signal-surfaces_open_harness_hub,
  title  = {Specialized model signal surfaces},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/specialized-model-signal-surfaces},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/specialized-model-signal-surfaces`.
