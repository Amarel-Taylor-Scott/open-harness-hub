---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- finance
- government
- ingestion-target
- knowledge-pack
- open-harness-hub
- rag_vector
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Math Misconception Taxonomy Bank
---

# Math Misconception Taxonomy Bank

<!-- Generated from Open Harness Hub manifest `knowledge-pack/math-misconception-taxonomy-bank` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: paraphrases free-text misconception instead of selecting canonical label; can't recall closed taxonomy Grounded in Eedi misconception_mapping.csv + distractor training data (CC) via rag_vector retrieval. Lift: winners used embedding retriever + reranker over fixed bank (MAP@25); turns generation into constrained NN lookup

**Industries**: finance, compliance, government
**Capabilities**: retrieval, verification
**Modalities**: structured, text
**Freshness**: volatile
**Trust boundary**: external

## Content types (leaf vocabulary)

- `fact_table`
- `reference_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/esoteric-packs/math-misconception-taxonomy-bank.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: Eedi misconception_mapping.csv + distractor training data (CC)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/math-misconception-taxonomy-bank.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{math-misconception-taxonomy-bank_open_harness_hub,
  title  = {Math Misconception Taxonomy Bank},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/math-misconception-taxonomy-bank},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/math-misconception-taxonomy-bank`.
