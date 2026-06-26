---
license: CC-BY-4.0
tags:
- 21-cfr-11
- alcoa
- annex-11
- beta
- compliance
- gxp
- healthcare.pharmacy
- ich
- open-harness-hub
- pharma
- pharma.gxp
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: 21-CFR-11 + EU GMP Annex 11 + ICH + ALCOA+ regulatory pack
---

# 21-CFR-11 + EU GMP Annex 11 + ICH + ALCOA+ regulatory pack

<!-- Generated from OpenHubForAI manifest `knowledge-pack/gxp-21-cfr-11-guidelines` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite educational extracts of GxP electronic-records /
electronic-signatures / data-integrity guidance:
 - US FDA 21 CFR Part 11 (Subpart B — Electronic Records;
   Subpart C — Electronic Signatures)
 - EU GMP Annex 11 (Computerised Systems)
 - ICH Q9 (Quality Risk Management)
 - ICH Q10 (Pharmaceutical Quality System)
 - ALCOA+ data-integrity principles
 - PIC/S PI 041 (Good Practices for Data Management and Integrity)
 - FDA Data Integrity Guidance 2018

**Industries**: pharma, pharma.gxp, healthcare.pharmacy, compliance
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
| `data/gxp-pack/cfr-11-sections.jsonl` | jsonl | — |
| `data/gxp-pack/annex-11-and-alcoa.jsonl` | jsonl | — |

## Provenance

- **sources**: FDA 21 CFR Part 11 (composite extracts), EU GMP Annex 11 (composite extracts), ICH Q9 + Q10 (composite extracts), PIC/S PI 041-1 (2021), composite extracts, FDA Data Integrity & Compliance with cGMP guidance (Dec 2018)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts; not authoritative regulatory text.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/gxp-21-cfr-11-guidelines.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{gxp-21-cfr-11-guidelines_open_harness_hub,
  title  = {21-CFR-11 + EU GMP Annex 11 + ICH + ALCOA+ regulatory pack},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/gxp-21-cfr-11-guidelines},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/gxp-21-cfr-11-guidelines`.
