---
license: CC-BY-4.0
tags:
- ai
- ai-governance
- ai-rmf
- ai_governance
- ai_governance.nist_rmf
- compliance
- govern
- manage
- map
- measure
- nist
- open-harness-hub
- research
- retrieval
- risk-management
- security
- stable
- trustworthy-ai
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: NIST AI Risk Management Framework (AI RMF 1.0) — Functions, Categories,
  and Subcategories
---

# NIST AI Risk Management Framework (AI RMF 1.0) — Functions, Categories, and Subcategories

<!-- Generated from Open Harness Hub manifest `knowledge-pack/nist-ai-rmf-functions` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Structured reference corpus for the NIST AI Risk Management Framework (AI RMF 1.0,
January 2023). Covers all four core functions — GOVERN, MAP, MEASURE, MANAGE —
with their categories and subcategories, implementation tips, and trustworthiness
characteristics. Includes supplemental entries for Profiles, the Playbook, and
the Generative AI supplement (NIST AI 600-1). Suitable for AI governance harnesses,
compliance gap analysis, control mapping, and retrieval-augmented AI risk review.

**Industries**: ai, ai_governance, ai_governance.nist_rmf, compliance, security
**Capabilities**: retrieval, research
**Modalities**: text, structured
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/nist-ai-rmf-functions.jsonl` | jsonl | — |

## Provenance

- **sources**: NIST AI Risk Management Framework 1.0 (https://doi.org/10.6028/NIST.AI.100-1), NIST AI RMF Playbook (https://airc.nist.gov/Docs/1), NIST AI 600-1 Generative AI Supplement (https://doi.org/10.6028/NIST.AI.600-1)
- **collected_through**: 2026-05-26
- **collected_by**: Open Harness Hub research agent
- **anonymization**: none — all content is public-domain US government material; no PII

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/nist-ai-rmf-functions.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{nist-ai-rmf-functions_open_harness_hub,
  title  = {NIST AI Risk Management Framework (AI RMF 1.0) — Functions, Categories, and Subcategories},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/nist-ai-rmf-functions},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/nist-ai-rmf-functions`.
