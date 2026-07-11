---
license: CC-BY-4.0
tags:
- ai-governance
- ai_governance
- ai_governance.eu_act
- ai_governance.iso_42001
- ai_governance.nist_rmf
- beta
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
pretty_name: AI governance frameworks (EU AI Act + NIST AI RMF + ISO 42001 + GDPR
  Art 22)
---

# AI governance frameworks (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/ai-governance-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Regulation (EU) 2024/1689 + NIST AI RMF 1.0 + ISO/IEC 42001:2023 + GDPR Art 22 + serious incident reporting.

**Industries**: ai_governance, ai_governance.eu_act, ai_governance.nist_rmf, ai_governance.iso_42001
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/ai-governance-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Regulation (EU) 2024/1689 AI Act (composite), NIST AI RMF 1.0 (composite), ISO/IEC 42001:2023 AIMS (composite), Regulation (EU) 2016/679 GDPR Art 22 (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/ai-governance-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{ai-governance-frameworks_open_harness_hub,
  title  = {AI governance frameworks (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/ai-governance-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/ai-governance-frameworks`.
