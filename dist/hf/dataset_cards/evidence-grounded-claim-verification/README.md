---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- experimental
- ingestion-target
- knowledge-pack
- open-harness-hub
- rag_vector
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Evidence Grounded Claim Verification
---

# Evidence Grounded Claim Verification

<!-- Generated from OpenHubForAI manifest `knowledge-pack/evidence-grounded-claim-verification` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: guesses SUPPORTED/REFUTED from priors; can't weigh evidence, esp. NOT-ENOUGH-INFO Grounded in FEVER claims + Wikipedia evidence (CC BY-SA, 1803.05355) via rag_vector retrieval. Lift: FEVER: closed-book LLMs poor (NEI class); retrieval + sentence entailment supplies auditable evidence

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
| `data/esoteric-packs/evidence-grounded-claim-verification.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: FEVER claims + Wikipedia evidence (CC BY-SA, 1803.05355)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/evidence-grounded-claim-verification.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{evidence-grounded-claim-verification_open_harness_hub,
  title  = {Evidence Grounded Claim Verification},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/evidence-grounded-claim-verification},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/evidence-grounded-claim-verification`.
