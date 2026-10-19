---
license: MIT
tags:
- compliance
- cross_industry
- esg
- experimental
- lead-company-code
- open-harness-hub
- placeholder
- retrieval
- stub
- supply_chain
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Lead-company code-of-conduct stub (placeholder)
---

# Lead-company code-of-conduct stub (placeholder)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/lead-company-code-stub` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Placeholder reference that ESG / vendor pipelines accept as the
lead-company-specific code of conduct. Real instances would replace
this with the deploying organization's actual code (a vendor-
required policy component).

Ships with one composite example entry — enough for pipelines to
pass validation in synthetic-demo mode without exposing a real
company's policy.

**Industries**: cross_industry, esg, supply_chain, compliance
**Capabilities**: retrieval
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/lead-company-code-stub.jsonl` | jsonl | — |

## Provenance

- **sources**: Composite placeholder — deploying organizations replace with their own code of conduct
- **collected_through**: 2026-05-20
- **note**: Stub for demo / testing only.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/lead-company-code-stub.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{lead-company-code-stub_open_harness_hub,
  title  = {Lead-company code-of-conduct stub (placeholder)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/lead-company-code-stub},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `knowledge-pack/lead-company-code-stub`.
