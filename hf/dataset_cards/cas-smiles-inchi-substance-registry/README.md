---
license: CC-BY-4.0
tags:
- capability-lift
- esoteric
- exact_id
- experimental
- ingestion-target
- knowledge-pack
- manufacturing
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
pretty_name: Cas Smiles Inchi Substance Registry
---

# Cas Smiles Inchi Substance Registry

<!-- Generated from Open Harness Hub manifest `knowledge-pack/cas-smiles-inchi-substance-registry` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: wrong CAS numbers, invalid/non-canonical SMILES/InChI, miscomputed InChIKeys Grounded in PubChem (public domain) + EPA CompTox + IUPAC InChI via exact_id retrieval. Lift: machine-validatable identifiers (InChIKey hashes, SMILES parseability) not derivable

**Industries**: manufacturing
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
| `data/esoteric-packs/cas-smiles-inchi-substance-registry.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: PubChem (public domain) + EPA CompTox + IUPAC InChI
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/cas-smiles-inchi-substance-registry.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{cas-smiles-inchi-substance-registry_open_harness_hub,
  title  = {Cas Smiles Inchi Substance Registry},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/cas-smiles-inchi-substance-registry},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/cas-smiles-inchi-substance-registry`.
