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
pretty_name: Essay Scoring Rubric Anchors And Qwk Calibration
---

# Essay Scoring Rubric Anchors And Qwk Calibration

<!-- Generated from OpenHubForAI manifest `knowledge-pack/essay-scoring-rubric-anchors-and-qwk-calibration` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: inconsistent absolute 1-6 grading, miscalibrated to score distribution, hurts QWK Grounded in Learning Agency Lab AES 2.0 + ASAP + CommonLit + rubrics (public) via rag_vector retrieval. Lift: winners regressed w/ rubric-anchored exemplars + QWK threshold opt; anchor+calibration lifts QWK

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
| `data/esoteric-packs/essay-scoring-rubric-anchors-and-qwk-calibration.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: Learning Agency Lab AES 2.0 + ASAP + CommonLit + rubrics (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/essay-scoring-rubric-anchors-and-qwk-calibration.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{essay-scoring-rubric-anchors-and-qwk-calibration_open_harness_hub,
  title  = {Essay Scoring Rubric Anchors And Qwk Calibration},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/essay-scoring-rubric-anchors-and-qwk-calibration},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/essay-scoring-rubric-anchors-and-qwk-calibration`.
