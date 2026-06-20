---
license: CC-BY-4.0
tags:
- beta
- ccpa
- compliance
- cpra
- e-privacy
- edpb
- gdpr
- open-harness-hub
- privacy
- privacy.ccpa
- privacy.dsar
- privacy.gdpr
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: GDPR articles + CCPA/CPRA + e-Privacy
---

# GDPR articles + CCPA/CPRA + e-Privacy

<!-- Generated from Open Harness Hub manifest `knowledge-pack/gdpr-articles-and-ccpa` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite educational extracts of:
 - EU GDPR (Regulation 2016/679) — Articles 5 / 6 / 7 / 9 /
   12-22 (data subject rights) / 25 (privacy by design) / 30
   (records of processing) / 32 (security) / 33-34 (breach) /
   35 (DPIA) / 44-49 (transfers) / 82 (compensation) / 83
   (administrative fines)
 - CCPA (Cal. Civ. Code §1798.100 et seq.) + CPRA amendments
 - EU e-Privacy Directive (cookies + e-marketing)
 - EDPB Guidelines on DSAR (2022)

**Industries**: privacy, privacy.gdpr, privacy.ccpa, privacy.dsar, compliance
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `citation_edge`

## Files

| path | format | schema |
|---|---|---|
| `data/gdpr-pack/gdpr-articles.jsonl` | jsonl | — |

## Provenance

- **sources**: EU GDPR (Reg. 2016/679) (composite extracts), CCPA/CPRA (Cal. Civ. Code §1798.100) (composite), EU e-Privacy Directive (composite), EDPB Guidelines 01/2022 on DSAR (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts; not authoritative legal text.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/gdpr-articles-and-ccpa.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{gdpr-articles-and-ccpa_open_harness_hub,
  title  = {GDPR articles + CCPA/CPRA + e-Privacy},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/gdpr-articles-and-ccpa},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/gdpr-articles-and-ccpa`.
