---
license: CC-BY-4.0
tags:
- agriculture
- agriculture_compliance
- agriculture_compliance.fsma
- agriculture_compliance.organic
- beta
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
pretty_name: Agriculture compliance frameworks (FSMA + USDA NOP + GAP + GlobalGAP)
---

# Agriculture compliance frameworks (FSMA + USDA NOP + GAP + GlobalGAP)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/agriculture-compliance-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

FSMA Produce Safety Rule + NOP organic + GlobalGAP + EPA pesticide labeling.

**Industries**: agriculture_compliance, agriculture_compliance.fsma, agriculture_compliance.organic
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/agriculture-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: 21 CFR Part 112 FSMA Produce Safety Rule (composite), 7 CFR Part 205 NOP (composite), GlobalGAP IFA v6 (composite), EPA FIFRA pesticide labeling (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/agriculture-compliance-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{agriculture-compliance-frameworks_open_harness_hub,
  title  = {Agriculture compliance frameworks (FSMA + USDA NOP + GAP + GlobalGAP)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/agriculture-compliance-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/agriculture-compliance-frameworks`.
