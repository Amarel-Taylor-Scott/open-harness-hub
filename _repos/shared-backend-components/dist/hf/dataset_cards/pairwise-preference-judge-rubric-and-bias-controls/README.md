---
license: CC-BY-4.0
tags:
- capability-lift
- classifier
- cross_industry
- esoteric
- experimental
- ingestion-target
- knowledge-pack
- open-harness-hub
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Pairwise Preference Judge Rubric And Bias Controls
---

# Pairwise Preference Judge Rubric And Bias Controls

<!-- Generated from OpenHubForAI manifest `knowledge-pack/pairwise-preference-judge-rubric-and-bias-controls` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: position/length/self-preference bias; miscalibrated to human-vote distribution Grounded in LMSYS Chatbot Arena + WSDM multilingual preference data (CC) via classifier retrieval. Lift: top solutions fine-tuned calibrated classifier w/ order-swap + length-debias; lowers log-loss vs human votes

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
| `data/esoteric-packs/pairwise-preference-judge-rubric-and-bias-controls.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: LMSYS Chatbot Arena + WSDM multilingual preference data (CC)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/pairwise-preference-judge-rubric-and-bias-controls.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{pairwise-preference-judge-rubric-and-bias-controls_open_harness_hub,
  title  = {Pairwise Preference Judge Rubric And Bias Controls},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/pairwise-preference-judge-rubric-and-bias-controls},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/pairwise-preference-judge-rubric-and-bias-controls`.
