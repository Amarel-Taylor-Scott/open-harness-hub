---
license: CC-BY-4.0
tags:
- experimental
- open-harness-hub
- privacy
- privacy-dpia-transfer
- privacy.gdpr
- privacy.pia
- retrieval
- synthetic-expansion
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Privacy DPIA Transfer frameworks
---

# Privacy DPIA Transfer frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/privacy-dpia-transfer-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite reference pack covering GDPR DPIA risk assessment, SCC transfer impact assessment, data minimization and retention, processor due diligence.

**Industries**: privacy, privacy.pia, privacy.gdpr
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `policy_summary`

## Files

| path | format | schema |
|---|---|---|
| `data/privacy-dpia-transfer/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: GDPR DPIA risk assessment, SCC transfer impact assessment, data minimization and retention, processor due diligence
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/privacy-dpia-transfer-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{privacy-dpia-transfer-frameworks_open_harness_hub,
  title  = {Privacy DPIA Transfer frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/privacy-dpia-transfer-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/privacy-dpia-transfer-frameworks`.
