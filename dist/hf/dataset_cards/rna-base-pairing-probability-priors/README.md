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
pretty_name: Rna Base Pairing Probability Priors
---

# Rna Base Pairing Probability Priors

<!-- Generated from OpenHubForAI manifest `knowledge-pack/rna-base-pairing-probability-priors` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: per-nucleotide reactivity depends on base-pairing structure (stems/loops/BPP); LLM can't fold Grounded in Stanford Ribonanza reactivity (CC) + RNA secondary-structure/BPP conventions (ViennaRNA-style, public) via graph retrieval. Lift: winning fed BPP matrices + structure-aware attention (MAE); BPP/structure-prior encodes the pairing graph

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
| `data/esoteric-packs/rna-base-pairing-probability-priors.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: Stanford Ribonanza reactivity (CC) + RNA secondary-structure/BPP conventions (ViennaRNA-style, public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/rna-base-pairing-probability-priors.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{rna-base-pairing-probability-priors_open_harness_hub,
  title  = {Rna Base Pairing Probability Priors},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/rna-base-pairing-probability-priors},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/rna-base-pairing-probability-priors`.
