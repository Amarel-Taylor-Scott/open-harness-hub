---
license: CC-BY-4.0
tags:
- beta
- cbp-wro
- classification
- compliance
- deforestation
- esg
- high-risk-corridor
- humanitarian
- kafala
- open-harness-hub
- retrieval
- supply_chain
- uflpa
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: High-risk corridors & sector-specific labor / environmental risks
---

# High-risk corridors & sector-specific labor / environmental risks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/high-risk-corridors-and-sectors` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite reference of high-risk geographic corridors and product
sectors with documented patterns of forced labor, child labor,
environmental harm, or governance opacity. Used by
`pipeline/supplier-policy-grading` and `pipeline/deep-tier-supplier-
audit` to up-weight findings when the supplier sources from listed
corridors / sectors.

Each entry includes: corridor name + indicative geography + product
sectors + documented risk categories + citations to the regulatory
basis for heightened review (UFLPA WROs, CBP findings list, ILO
country reports, US TVPA Tier rankings).

Categories covered:
 - **Apparel / textile**: Xinjiang (cotton, UFLPA), Sialkot
   (Pakistan, sports goods), Bangladesh (Ashulia, Narayanganj),
   Cambodia (Phnom Penh), Vietnam, Myanmar
 - **Electronics / minerals**: DRC (cobalt — Katanga, Kolwezi,
   Likasi), Indonesia (tin — Bangka), Colombia (gold), Peru
   (gold), Madagascar (mica), India (Jharkhand mica)
 - **Agriculture**: Côte d'Ivoire + Ghana (cocoa, child labor),
   Brazil (beef + Amazon deforestation), Paraguay + Argentina
   (soy, Gran Chaco deforestation), Malaysia + Indonesia
   (palm oil, RSPO gaps), Uzbekistan (cotton, formerly state-
   compelled), Turkmenistan (cotton)
 - **Construction / domestic work**: Gulf states (Qatar, Saudi
   Arabia, UAE, Kuwait, Bahrain — kafala system), Singapore
   (migrant construction)
 - **Seafood**: Thailand (Samut Sakhon, Ranong — fishing vessels),
   Bangladesh (shrimp), Vietnam
 - **Brick kilns**: India (Bihar, UP), Pakistan (Punjab), Nepal,
   Cambodia
 - **Carpets / glass / footwear**: Pakistan (Sialkot), India
   (Bhainsa carpets, Firozabad glass), Bangladesh

Composite educational extracts; supplier mapping requires real-
time CBP WRO / UFLPA Entity List checks (which change frequently).

**Industries**: esg, supply_chain, compliance, humanitarian
**Capabilities**: retrieval, classification
**Modalities**: text
**Freshness**: volatile
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `classifier_rule`

## Files

| path | format | schema |
|---|---|---|
| `data/corridors-pack/corridors.jsonl` | jsonl | — |
| `data/corridors-pack/cbp-wro-uflpa-snapshot.jsonl` | jsonl | — |

## Provenance

- **sources**: US CBP Withhold Release Orders (https://www.cbp.gov/trade/forced-labor) — snapshot 2026-04-30, US UFLPA Entity List — snapshot 2026-04-30, ILO Better Work program country reports, ITUC Global Rights Index 2025, US State Department TIP Report 2025 country tier rankings, Verité commodity Atlas (apparel, electronics, agriculture)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts; live CBP WRO + UFLPA Entity List checks via `tool/cbp-wro-lookup` (planned). Corridor coverage is non-exhaustive.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/high-risk-corridors-and-sectors.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{high-risk-corridors-and-sectors_open_harness_hub,
  title  = {High-risk corridors & sector-specific labor / environmental risks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/high-risk-corridors-and-sectors},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub artifact: `knowledge-pack/high-risk-corridors-and-sectors`.
