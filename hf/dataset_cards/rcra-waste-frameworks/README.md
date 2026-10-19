---
license: CC-BY-4.0
tags:
- beta
- open-harness-hub
- rcra
- retrieval
- verification
- waste
- waste.generator
- waste.rcra_tsdf
- waste.universal
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: RCRA hazardous waste frameworks (40 CFR 260-279 + e-Manifest + DOT 49
  CFR 172)
---

# RCRA hazardous waste frameworks (40 CFR 260-279 + e-Manifest + DOT 49 CFR 172)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/rcra-waste-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

RCRA Subtitle C identification + generator + transporter + TSDF + LDR + Universal Waste + Used Oil + DOT HMR.

**Industries**: waste, waste.rcra_tsdf, waste.generator, waste.universal
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/rcra-waste-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: 40 CFR Parts 260-279 RCRA Subtitle C (composite), EPA e-Manifest Form 8700-22 (composite), DOT 49 CFR 172 HMR (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/rcra-waste-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{rcra-waste-frameworks_open_harness_hub,
  title  = {RCRA hazardous waste frameworks (40 CFR 260-279 + e-Manifest + DOT 49 CFR 172)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/rcra-waste-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/rcra-waste-frameworks`.
