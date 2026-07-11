---
license: CC-BY-4.0
tags:
- ai
- classification
- cross_industry
- dimensions
- experimental
- governance
- hybrid-search
- labels
- open-harness-hub
- pgvector
- reranking
- retrieval
- schema-org
- software.devops
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Hybrid label and dimension taxonomy
---

# Hybrid label and dimension taxonomy

<!-- Generated from OpenHubForAI manifest `knowledge-pack/hybrid-label-dimension-taxonomy` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Label sets, schema.org-style mappings, hierarchical paths, and generated dimension definitions for hybrid keyword, vector, graph, and model-polished search.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: retrieval, classification, reranking, governance
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: hub

## Content types (leaf vocabulary)

- `label_set`
- `dimension_definition`
- `schema_org_mapping`
- `hierarchical_label`

## Files

| path | format | schema |
|---|---|---|
| `data/hybrid-label-dimension-taxonomy/labels.jsonl` | jsonl | — |

## Provenance

- **sources**: OpenHubForAI hybrid label and dimensional search architecture, schema.org concept vocabulary
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: synthetic taxonomy records only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/hybrid-label-dimension-taxonomy.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{hybrid-label-dimension-taxonomy_open_harness_hub,
  title  = {Hybrid label and dimension taxonomy},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/hybrid-label-dimension-taxonomy},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/hybrid-label-dimension-taxonomy`.
