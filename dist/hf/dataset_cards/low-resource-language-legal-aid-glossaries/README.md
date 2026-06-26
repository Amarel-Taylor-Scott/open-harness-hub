---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- ingestion-target
- keyword
- knowledge-pack
- legal
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
pretty_name: Low Resource Language Legal Aid Glossaries
---

# Low Resource Language Legal Aid Glossaries

<!-- Generated from OpenHubForAI manifest `knowledge-pack/low-resource-language-legal-aid-glossaries` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: models mistranslate legal/administrative terms in under-resourced languages, producing dangerous errors in rights, eligibility, and procedure Grounded in community-validated bilingual legal glossaries + UNTERM + national legal-aid bodies (reusable w/ attribution) via keyword retrieval. Lift: low data coverage (under-resourced languages) = valley; exact term mappings verifiable and token-efficient (substitute long phrases)

**Industries**: legal, compliance
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
| `data/esoteric-packs/low-resource-language-legal-aid-glossaries.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: community-validated bilingual legal glossaries + UNTERM + national legal-aid bodies (reusable w/ attribution)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/low-resource-language-legal-aid-glossaries.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{low-resource-language-legal-aid-glossaries_open_harness_hub,
  title  = {Low Resource Language Legal Aid Glossaries},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/low-resource-language-legal-aid-glossaries},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/low-resource-language-legal-aid-glossaries`.
