---
license: CC-BY-4.0
tags:
- beta
- defense
- defense.cmmc
- defense.counterfeit_parts
- defense.dfars
- dfars
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
pretty_name: Defense compliance frameworks (DFARS / FAR / CMMC / NIST 800-171 / SAE
  AS5553 / Section 889)
---

# Defense compliance frameworks (DFARS / FAR / CMMC / NIST 800-171 / SAE AS5553 / Section 889)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/defense-dfars-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite of US DoD acquisition + cyber + counterfeit-parts compliance.

**Industries**: defense, defense.dfars, defense.cmmc, defense.counterfeit_parts
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/defense-pack/dfars-cmmc.jsonl` | jsonl | — |

## Provenance

- **sources**: DFARS subparts 204, 225, 246 (composite), CMMC 2.0 model (composite), NIST SP 800-171 controls (composite), SAE AS5553 + AS6081 counterfeit-parts (composite), Section 889 telecom prohibition (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/defense-dfars-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{defense-dfars-frameworks_open_harness_hub,
  title  = {Defense compliance frameworks (DFARS / FAR / CMMC / NIST 800-171 / SAE AS5553 / Section 889)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/defense-dfars-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/defense-dfars-frameworks`.
