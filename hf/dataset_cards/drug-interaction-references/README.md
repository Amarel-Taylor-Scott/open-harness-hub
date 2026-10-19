---
license: CC-BY-4.0
tags:
- drug-interactions
- experimental
- healthcare
- healthcare.pharmacy
- medlabel
- open-harness-hub
- patient-safety
- pharmacy
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Drug-drug interaction references (DrugBank / RxNorm / FDA Orange Book
  / DailyMed)
---

# Drug-drug interaction references (DrugBank / RxNorm / FDA Orange Book / DailyMed)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/drug-interaction-references` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite educational reference of drug-drug interaction sources
for use by `pipeline/medlabel-photo-to-warning` and similar
medicine-safety AI pipelines.

This is a STUB knowledge pack — the actual production drug-
interaction database requires licensing from authoritative
pharmacology sources (DrugBank, Micromedex, Lexicomp, Stockley's
Drug Interactions). The catalog's role is the shape + the
attribution + the citation requirement (every severe interaction
finding MUST cite the authoritative source).

**Industries**: healthcare, healthcare.pharmacy
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/medlabel-pack/drug-interaction-examples.jsonl` | jsonl | — |

## Provenance

- **sources**: DrugBank Online (educational; requires academic / commercial license for production), RxNorm (NIH NLM — public), FDA Orange Book (public), DailyMed labels (public, FDA), Stockley's Drug Interactions (commercial reference)
- **collected_through**: 2026-05-21
- **note**: Production deployments must use a licensed, regularly-updated drug-interaction database. This stub provides the SHAPE — not authoritative content.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/drug-interaction-references.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{drug-interaction-references_open_harness_hub,
  title  = {Drug-drug interaction references (DrugBank / RxNorm / FDA Orange Book / DailyMed)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/drug-interaction-references},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/drug-interaction-references`.
