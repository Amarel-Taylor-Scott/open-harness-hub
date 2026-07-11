---
license: MIT
tags:
- compliance
- ear
- evaluation
- experimental
- itar
- open-harness-hub
- synthetic
- trade
- trade.eccn
- trade.itar
- trade.sanctions
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Synthetic trade-export transaction samples
---

# Synthetic trade-export transaction samples

<!-- Generated from OpenHubForAI manifest `dataset/trade-export-samples` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Two synthetic exports:
 - clean: standard laptops to Singapore, EAR99, B-list destination,
   no Entity-list hits, no license required. Expected 0 hits.
 - flagged: Iran destination, Russia onward via HK transshipment,
   Entity List hit, ITAR technical data, deemed-export to H-1B,
   OFAC SDN match on freight forwarder, surveillance tech to MoI,
   dual-use to MEU, cash payment, no end-user cert. Expected many
   critical hits.

**Industries**: trade, trade.eccn, trade.itar, trade.sanctions, compliance
**Capabilities**: evaluation
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Provenance

- **origin**: Fully synthetic
- **collected_by**: OpenHubForAI contributors
- **collected_through**: 2026-05-20
- **license**: MIT
- **anonymization**: fully synthetic

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/trade-export-samples.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{trade-export-samples_open_harness_hub,
  title  = {Synthetic trade-export transaction samples},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/dataset/trade-export-samples},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `dataset/trade-export-samples`.
