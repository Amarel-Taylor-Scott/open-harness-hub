---
license: MIT
tags:
- compliance
- csddd
- csrd
- esg
- evaluation
- experimental
- open-harness-hub
- schema
- supplier-disclosure
- supply_chain
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Supplier disclosure pack schema (canonical input shape)
---

# Supplier disclosure pack schema (canonical input shape)

<!-- Generated from Open Harness Hub manifest `dataset/supplier-disclosure-pack-schema` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Canonical input shape that `pipeline/supplier-policy-grading` and
`pipeline/deep-tier-supplier-audit` accept as the supplier
disclosure pack. Records the JSON Schema of the supplier-submitted
artifact so compliance teams can prepare their data once and feed
it into any pipeline in the ESG vertical.

The pack covers: supplier identity + tier + UBO + geography + sector
+ policy texts + self-assessment + grievance summary + audit reports
+ GHG inventory + EUDR-relevant commodities geolocation + worker
representation. Each section is OPTIONAL — pipelines flag missing
required-for-jurisdiction sections rather than fail.

Includes 3 sample disclosure packs for testing:
 - sample-T1-tech-supplier-good.json (a well-disclosed T1 supplier)
 - sample-T3-textile-mae-sot-flagged.json (a T3 supplier with
   forced-labor + corridor red flags)
 - sample-T2-agri-paraguay-mixed.json (a T2 soy supplier with
   mixed signals: strong S, weak E around deforestation)

**Industries**: esg, supply_chain, compliance
**Capabilities**: evaluation
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: local

## Provenance

- **origin**: Composite synthetic disclosures (not real suppliers)
- **collected_by**: Open Harness Hub contributors
- **collected_through**: 2026-05-19
- **license**: MIT
- **anonymization**: fully synthetic — no real-supplier data

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/supplier-disclosure-pack-schema.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{supplier-disclosure-pack-schema_open_harness_hub,
  title  = {Supplier disclosure pack schema (canonical input shape)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/dataset/supplier-disclosure-pack-schema},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub artifact: `dataset/supplier-disclosure-pack-schema`.
