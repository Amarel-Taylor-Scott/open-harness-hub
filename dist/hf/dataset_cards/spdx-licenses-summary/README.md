---
license: CC0-1.0
tags:
- compliance
- cross_industry
- legal
- licenses
- open-harness-hub
- retrieval
- software
- spdx
- stable
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: SPDX licenses (summary)
---

# SPDX licenses (summary)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/spdx-licenses-summary` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Sampled summary of common SPDX licenses — permissive, copyleft,
non-commercial, public-domain. For each: license_id, category,
one-paragraph summary, redistribution-compatible flag, derivative
work permitted flag. Use the full SPDX list at spdx.org/licenses
for production.

**Industries**: cross_industry, legal, software
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/spdx-licenses-summary.jsonl` | jsonl | — |

## Provenance

- **sources**: SPDX License List (https://spdx.org/licenses/)
- **collected_through**: 2026-04-30

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/spdx-licenses-summary.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{spdx-licenses-summary_open_harness_hub,
  title  = {SPDX licenses (summary)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/spdx-licenses-summary},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC0-1.0`. Hub artifact: `knowledge-pack/spdx-licenses-summary`.
