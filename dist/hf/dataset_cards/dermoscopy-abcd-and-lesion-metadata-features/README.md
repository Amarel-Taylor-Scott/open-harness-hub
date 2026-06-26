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
pretty_name: Dermoscopy Abcd And Lesion Metadata Features
---

# Dermoscopy Abcd And Lesion Metadata Features

<!-- Generated from OpenHubForAI manifest `knowledge-pack/dermoscopy-abcd-and-lesion-metadata-features` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: malignancy needs dermoscopic ABCD/7-point + patient metadata + ugly-duckling context Grounded in ISIC Archive images+metadata (CC) + ABCD/7-point checklists (clinical lit) via classifier retrieval. Lift: top fused image + tabular + within-patient under partial-AUC; feature+metadata schema produced the lift

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
| `data/esoteric-packs/dermoscopy-abcd-and-lesion-metadata-features.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: ISIC Archive images+metadata (CC) + ABCD/7-point checklists (clinical lit)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/dermoscopy-abcd-and-lesion-metadata-features.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{dermoscopy-abcd-and-lesion-metadata-features_open_harness_hub,
  title  = {Dermoscopy Abcd And Lesion Metadata Features},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/dermoscopy-abcd-and-lesion-metadata-features},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/dermoscopy-abcd-and-lesion-metadata-features`.
