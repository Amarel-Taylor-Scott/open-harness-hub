---
license: CC-BY-4.0
tags:
- acrac
- beta
- bi-rads
- fleischner
- healthcare
- healthcare.clinical
- healthcare.radiology
- li-rads
- lung-rads
- o-rads
- open-harness-hub
- pi-rads
- radiology
- retrieval
- ti-rads
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: ACR Appropriateness Criteria + Fleischner + ACR RADS rubrics
---

# ACR Appropriateness Criteria + Fleischner + ACR RADS rubrics

<!-- Generated from Open Harness Hub manifest `knowledge-pack/radiology-acrac-fleischner` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite, educational extracts of radiology citation backbone:

 - ACR Appropriateness Criteria (selected high-volume topics):
   headache, low back pain, acute abdominal pain, suspected
   pulmonary embolism, pulmonary nodule incidental.
 - Fleischner Society 2017 guidelines for pulmonary nodule
   management (solid + sub-solid, single + multiple).
 - ACR Reporting and Data Systems (RADS):
   * BI-RADS 6th ed. (breast: 0-6 + density categories a-d)
   * LI-RADS v2018 (liver: LR-1 → LR-5, LR-M, LR-TIV)
   * TI-RADS ACR (thyroid: TR1-TR5)
   * O-RADS US + MRI (ovarian/adnexal)
   * PI-RADS v2.1 (prostate MRI)
   * Lung-RADS 1.1 (lung cancer screening)
   * NI-RADS (head & neck post-treatment)
 - RSNA reporting templates (structured-reporting standard).
 - Common abbreviations + impression language conventions.

Composite educational extracts; clinical use requires the radiologist's
professional judgment + access to the authoritative current ACR/RSNA
publications.

**Industries**: healthcare, healthcare.radiology, healthcare.clinical
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
| `data/radiology-pack/acrac-selected.jsonl` | jsonl | — |
| `data/radiology-pack/fleischner-2017.jsonl` | jsonl | — |
| `data/radiology-pack/rads-scoring.jsonl` | jsonl | — |

## Provenance

- **sources**: ACR Appropriateness Criteria (composite educational extracts), Fleischner Society 2017 incidental pulmonary nodule guidelines (composite), ACR BI-RADS / LI-RADS / TI-RADS / O-RADS / PI-RADS / Lung-RADS / NI-RADS (composite), RSNA RadReport structured-reporting templates (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts; not authoritative clinical text.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/radiology-acrac-fleischner.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{radiology-acrac-fleischner_open_harness_hub,
  title  = {ACR Appropriateness Criteria + Fleischner + ACR RADS rubrics},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/radiology-acrac-fleischner},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub artifact: `knowledge-pack/radiology-acrac-fleischner`.
