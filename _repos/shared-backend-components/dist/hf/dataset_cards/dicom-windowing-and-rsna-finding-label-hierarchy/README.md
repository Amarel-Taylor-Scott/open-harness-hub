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
pretty_name: Dicom Windowing And Rsna Finding Label Hierarchy
---

# Dicom Windowing And Rsna Finding Label Hierarchy

<!-- Generated from OpenHubForAI manifest `knowledge-pack/dicom-windowing-and-rsna-finding-label-hierarchy` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: CT/MR findings need DICOM windowing, slice-volume context, hierarchical label schema Grounded in RSNA DICOM + label hierarchies (research/CC) + HU window presets + finding ontologies (public) via classifier retrieval. Lift: winners depended on windowing + hierarchy-aware heads (weighted log-loss); component encodes the structure

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
| `data/esoteric-packs/dicom-windowing-and-rsna-finding-label-hierarchy.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: RSNA DICOM + label hierarchies (research/CC) + HU window presets + finding ontologies (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/dicom-windowing-and-rsna-finding-label-hierarchy.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{dicom-windowing-and-rsna-finding-label-hierarchy_open_harness_hub,
  title  = {Dicom Windowing And Rsna Finding Label Hierarchy},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/dicom-windowing-and-rsna-finding-label-hierarchy},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/dicom-windowing-and-rsna-finding-label-hierarchy`.
