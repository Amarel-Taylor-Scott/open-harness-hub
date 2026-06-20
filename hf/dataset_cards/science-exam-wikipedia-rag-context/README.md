---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- experimental
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
pretty_name: Science Exam Wikipedia Rag Context
---

# Science Exam Wikipedia Rag Context

<!-- Generated from Open Harness Hub manifest `knowledge-pack/science-exam-wikipedia-rag-context` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: hallucinates on long-tail science MCQs; lift came from retrieving Wikipedia passages Grounded in Kaggle LLM Science Exam + STEM Wikipedia (CC-BY-SA) via rag_vector retrieval. Lift: decisive move was Wikipedia FAISS retriever feeding context; packaged index lifts MAP@3 over closed-book

**Industries**: cross_industry
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
| `data/esoteric-packs/science-exam-wikipedia-rag-context.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: Kaggle LLM Science Exam + STEM Wikipedia (CC-BY-SA)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/science-exam-wikipedia-rag-context.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{science-exam-wikipedia-rag-context_open_harness_hub,
  title  = {Science Exam Wikipedia Rag Context},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/science-exam-wikipedia-rag-context},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/science-exam-wikipedia-rag-context`.
