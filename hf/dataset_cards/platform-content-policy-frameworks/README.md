---
license: CC-BY-4.0
tags:
- beta
- compliance
- coppa
- dsa
- media
- open-harness-hub
- platform
- privacy
- retrieval
- trust-and-safety
- uk-osa
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Platform content policy frameworks (DSA + UK OSA + COPPA + NetzDG)
---

# Platform content policy frameworks (DSA + UK OSA + COPPA + NetzDG)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/platform-content-policy-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite reference for platform-side moderation policy: EU Digital Services Act, UK Online Safety Act 2023, US COPPA, US Section 230 limits, German NetzDG, NCMEC CyberTipline obligations, GIFCT terrorist content hash sharing. Use as the policy backstop for trust + safety pipelines.

**Industries**: compliance, media, privacy
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/platform-policy-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Regulation (EU) 2022/2065 DSA (composite), UK Online Safety Act 2023 (composite), 15 USC §§ 6501-6506 COPPA (composite), 47 USC §230 (composite), NetzDG (composite), 18 USC §2258A NCMEC reporting (composite), GIFCT Hash Sharing Database (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts; consult primary law for compliance work.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/platform-content-policy-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{platform-content-policy-frameworks_open_harness_hub,
  title  = {Platform content policy frameworks (DSA + UK OSA + COPPA + NetzDG)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/platform-content-policy-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/platform-content-policy-frameworks`.
