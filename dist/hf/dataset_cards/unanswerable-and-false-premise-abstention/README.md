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
pretty_name: Unanswerable And False Premise Abstention
---

# Unanswerable And False Premise Abstention

<!-- Generated from OpenHubForAI manifest `knowledge-pack/unanswerable-and-false-premise-abstention` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: answers unanswerable/underspecified/false-premise instead of abstaining; poor calibration Grounded in SQuAD 2.0 (CC BY-SA, 1806.03822) + AbstentionBench (2506.09038) via classifier retrieval. Lift: AbstentionBench: even reasoning LLMs fail to abstain; answerability gate forces 'no supported answer'

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
| `data/esoteric-packs/unanswerable-and-false-premise-abstention.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: SQuAD 2.0 (CC BY-SA, 1806.03822) + AbstentionBench (2506.09038)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/unanswerable-and-false-premise-abstention.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{unanswerable-and-false-premise-abstention_open_harness_hub,
  title  = {Unanswerable And False Premise Abstention},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/unanswerable-and-false-premise-abstention},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/unanswerable-and-false-premise-abstention`.
