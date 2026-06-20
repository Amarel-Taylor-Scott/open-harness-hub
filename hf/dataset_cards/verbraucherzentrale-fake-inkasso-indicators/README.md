---
license: CC-BY-4.0
tags:
- beta
- bureaucracy_translation
- bureaucracy_translation.fraud_screening
- classification
- fake-inkasso
- fraud-detection
- germany
- humanitarian
- humanitarian.refugee
- inkasso
- kaggle-hackathon-verified
- open-harness-hub
- retrieval
- verbraucherzentrale
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Verbraucherzentrale Fake-Inkasso indicators (10-criterion taxonomy)
---

# Verbraucherzentrale Fake-Inkasso indicators (10-criterion taxonomy)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/verbraucherzentrale-fake-inkasso-indicators` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite educational reference of the Verbraucherzentrale's
published Fake-Inkasso indicators. Used by Sviatoslav Grabovsky's
Bill_info AI to classify German payment demands as legitimate /
suspicious / likely-scam.

Source authority: Verbraucherzentrale Brandenburg Schwarzliste
Inkasso (~191,000 page views in a single year; 400 reported
fake-Inkasso letters in 2022) + sibling Verbraucherzentrale
publications.

Criterion tiers:
- **CRITICAL** (any one alone may justify likely_scam):
   (1) foreign IBAN (non-DE/AT/CH)
   (2) private-person recipient (vs. registered company)
   (3) legal threats (Schufa, Gerichtsvollzieher) in a FIRST letter
   (4) extreme 24-72 hour deadline
- **SUPPORTING** (multiple → suspicious / likely_scam):
   (5) missing regulatory information
   (6) unclear / unnamed creditor
   (7) dubious / surprising fees
   (8) phantom company names
   (9) premium phone numbers
   (10) pressure tactics ("letzte Mahnung" in a first letter)

Three-level classification:
- **legitimate**: no UI change (no false alarms on real Inkasso)
- **suspicious**: yellow advisory + verification step prepended
  to recommendations
- **likely_scam**: red banner + recommendations completely
  overridden to "do not pay, verify via Verbraucherzentrale,
  save as evidence"

**Industries**: bureaucracy_translation, bureaucracy_translation.fraud_screening, humanitarian, humanitarian.refugee
**Capabilities**: retrieval, classification, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/bill-info-pack/verbraucherzentrale-fake-inkasso.jsonl` | jsonl | — |

## Provenance

- **sources**: Verbraucherzentrale Brandenburg Schwarzliste Inkasso (composite educational extracts), Sviatoslav Grabovsky's Bill_info AI implementation (huggingface.co/spaces/Svityk/bill-info-ai), Verbraucherzentrale Fake-Inkasso publications (composite)
- **collected_through**: 2026-05-21
- **note**: Composite educational extracts; check current Verbraucherzentrale publications for live indicators. The Schwarzliste Inkasso is the authoritative source for naming-and-shaming actual fake-Inkasso companies.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/verbraucherzentrale-fake-inkasso-indicators.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{verbraucherzentrale-fake-inkasso-indicators_open_harness_hub,
  title  = {Verbraucherzentrale Fake-Inkasso indicators (10-criterion taxonomy)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/verbraucherzentrale-fake-inkasso-indicators},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/verbraucherzentrale-fake-inkasso-indicators`.
