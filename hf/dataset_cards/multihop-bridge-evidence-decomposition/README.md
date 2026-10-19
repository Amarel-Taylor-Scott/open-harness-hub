---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- experimental
- graph
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
pretty_name: Multihop Bridge Evidence Decomposition
---

# Multihop Bridge Evidence Decomposition

<!-- Generated from Open Harness Hub manifest `knowledge-pack/multihop-bridge-evidence-decomposition` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: shortcuts multi-hop via single-hop cues; skips bridge entities Grounded in MuSiQue (CC BY 4.0, 2108.00573) + HotpotQA (CC BY-SA) via graph retrieval. Lift: MuSiQue shows large drops + disconnected-reasoning shortcuts; explicit bridge traversal supplies the chain

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
| `data/esoteric-packs/multihop-bridge-evidence-decomposition.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: MuSiQue (CC BY 4.0, 2108.00573) + HotpotQA (CC BY-SA)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/multihop-bridge-evidence-decomposition.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{multihop-bridge-evidence-decomposition_open_harness_hub,
  title  = {Multihop Bridge Evidence Decomposition},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/multihop-bridge-evidence-decomposition},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/multihop-bridge-evidence-decomposition`.
