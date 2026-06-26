---
license: CC-BY-4.0
tags:
- aviation
- aviation.safety
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
pretty_name: Aviation safety frameworks (NTSB / FAA / ICAO / HFACS / ASAP)
---

# Aviation safety frameworks (NTSB / FAA / ICAO / HFACS / ASAP)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/aviation-safety-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite — NTSB cause taxonomy + FAA AC 120-92 SMS + ICAO Annex 13 + HFACS framework + ASAP MOU principles.

**Industries**: aviation, aviation.safety
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/aviation-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: NTSB Cause Taxonomy (composite), FAA AC 120-92 SMS (composite), ICAO Annex 13 (composite), HFACS DoT-FAA-AM-00-7 (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/aviation-safety-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{aviation-safety-frameworks_open_harness_hub,
  title  = {Aviation safety frameworks (NTSB / FAA / ICAO / HFACS / ASAP)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/aviation-safety-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/aviation-safety-frameworks`.
