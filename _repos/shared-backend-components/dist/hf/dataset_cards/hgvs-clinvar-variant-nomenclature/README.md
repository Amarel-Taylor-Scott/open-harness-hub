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
pretty_name: Hgvs Clinvar Variant Nomenclature
---

# Hgvs Clinvar Variant Nomenclature

<!-- Generated from OpenHubForAI manifest `knowledge-pack/hgvs-clinvar-variant-nomenclature` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: invalid HGVS strings; mismap rsID/ClinVar significance; GRCh37/38 coordinate confusion Grounded in HGVS spec + NCBI ClinVar (public domain) + dbSNP via exact_id retrieval. Lift: regex-validatable grammar + fast-growing curated DB + build-specific coords

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
| `data/esoteric-packs/hgvs-clinvar-variant-nomenclature.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: HGVS spec + NCBI ClinVar (public domain) + dbSNP
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/hgvs-clinvar-variant-nomenclature.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{hgvs-clinvar-variant-nomenclature_open_harness_hub,
  title  = {Hgvs Clinvar Variant Nomenclature},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/hgvs-clinvar-variant-nomenclature},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/hgvs-clinvar-variant-nomenclature`.
