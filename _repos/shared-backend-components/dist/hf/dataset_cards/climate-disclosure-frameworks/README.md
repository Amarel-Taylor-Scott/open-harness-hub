---
license: CC-BY-4.0
tags:
- beta
- cdp
- climate
- esg
- esrs
- finance
- ghg-protocol
- issb
- open-harness-hub
- retrieval
- sbti
- tcfd
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Climate disclosure frameworks (TCFD + ISSB IFRS S2 + CDP + ESRS E1)
---

# Climate disclosure frameworks (TCFD + ISSB IFRS S2 + CDP + ESRS E1)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/climate-disclosure-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite educational extracts of the major climate-disclosure
frameworks:
 - TCFD (Task Force on Climate-related Financial Disclosures)
   recommendations across 4 pillars (Governance / Strategy /
   Risk Management / Metrics & Targets)
 - ISSB IFRS S2 (Climate-related Disclosures)
 - CDP Climate Change Questionnaire 2024 scoring methodology
 - EU CSRD ESRS E1 (Climate change)
 - SBTi criteria for science-based-target validation
 - GHG Protocol Corporate Standard (Scope 1/2/3)
 - GHG Protocol Scope 3 categories 1-15

**Industries**: climate, esg, finance
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
| `data/tcfd-pack/tcfd-issb-esrs.jsonl` | jsonl | — |

## Provenance

- **sources**: TCFD final recommendations (composite extracts), ISSB IFRS S2 (composite extracts), CDP Climate Change 2024 (composite extracts), EU CSRD ESRS E1 (composite extracts), SBTi target-setting criteria (composite extracts), GHG Protocol Corporate Standard (composite extracts)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts; not authoritative regulatory text.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/climate-disclosure-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{climate-disclosure-frameworks_open_harness_hub,
  title  = {Climate disclosure frameworks (TCFD + ISSB IFRS S2 + CDP + ESRS E1)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/climate-disclosure-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/climate-disclosure-frameworks`.
