---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- exact_id
- experimental
- government
- healthcare
- ingestion-target
- knowledge-pack
- open-harness-hub
- pharma
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Uniprot Pdb Protein Identifiers
---

# Uniprot Pdb Protein Identifiers

<!-- Generated from Open Harness Hub manifest `knowledge-pack/uniprot-pdb-protein-identifiers` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: hallucinate UniProt accessions, PDB ids, EC numbers, Pfam/InterPro domains Grounded in UniProtKB (CC-BY) + RCSB PDB (public domain) + ENZYME + InterPro via exact_id retrieval. Lift: millions of stable opaque ids not derivable by reasoning

**Industries**: healthcare, pharma, compliance, government
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
| `data/esoteric-packs/uniprot-pdb-protein-identifiers.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: UniProtKB (CC-BY) + RCSB PDB (public domain) + ENZYME + InterPro
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/uniprot-pdb-protein-identifiers.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{uniprot-pdb-protein-identifiers_open_harness_hub,
  title  = {Uniprot Pdb Protein Identifiers},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/uniprot-pdb-protein-identifiers},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/uniprot-pdb-protein-identifiers`.
