---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- exact_id
- experimental
- ingestion-target
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
pretty_name: Statute Citation And Crossref Grounding
---

# Statute Citation And Crossref Grounding

<!-- Generated from Open Harness Hub manifest `knowledge-pack/statute-citation-and-crossref-grounding` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: invents case/statute citations, fabricates reporter volumes/pinpoints, misresolves cross-refs Grounded in Caselaw Access Project (CC0) + US Code via Cornell LII/govinfo (public domain) via exact_id retrieval. Lift: court-sanctioned fabricated cites; resolve every citation against authoritative corpus

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
| `data/esoteric-packs/statute-citation-and-crossref-grounding.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: Caselaw Access Project (CC0) + US Code via Cornell LII/govinfo (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/statute-citation-and-crossref-grounding.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{statute-citation-and-crossref-grounding_open_harness_hub,
  title  = {Statute Citation And Crossref Grounding},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/statute-citation-and-crossref-grounding},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/statute-citation-and-crossref-grounding`.
