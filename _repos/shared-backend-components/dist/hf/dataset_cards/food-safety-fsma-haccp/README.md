---
license: CC-BY-4.0
tags:
- beta
- food-safety
- food_safety
- food_safety.fsma
- food_safety.haccp
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
pretty_name: FSMA + HACCP + GFSI food safety frameworks
---

# FSMA + HACCP + GFSI food safety frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/food-safety-fsma-haccp` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite — FDA FSMA rules (21 CFR 117 / FSVP / 112 / 121) + HACCP 7 principles + GFSI-recognized schemes (SQF / BRCGS / FSSC 22000) + FDA recall classes + FSMA-204 traceability.

**Industries**: food_safety, food_safety.fsma, food_safety.haccp
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/foodsafety-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: FDA FSMA rules (composite), Codex Alimentarius HACCP (composite), GFSI Benchmarking Requirements v2024 (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/food-safety-fsma-haccp.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{food-safety-fsma-haccp_open_harness_hub,
  title  = {FSMA + HACCP + GFSI food safety frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/food-safety-fsma-haccp},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/food-safety-fsma-haccp`.
