---
license: CC-BY-4.0
tags:
- climate
- compliance
- cross_industry
- esg
- esg.csrd
- experimental
- gri
- ifrs-s1
- ifrs-s2
- issb
- open-harness-hub
- retrieval
- sasb
- sbti
- sustainability
- tcfd
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Voluntary sustainability disclosure frameworks — SASB / GRI / TCFD /
  ISSB / SBTi
---

# Voluntary sustainability disclosure frameworks — SASB / GRI / TCFD / ISSB / SBTi

<!-- Generated from OpenHubForAI manifest `knowledge-pack/sasb-gri-tcfd-issb-standards` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Reference pack of (composite educational) extracts from the four
most-cited voluntary sustainability disclosure frameworks plus
SBTi:

**SASB (Sustainability Accounting Standards Board)**
 - 77 industry-specific standards organized under Sustainable
   Industry Classification System (SICS) — 11 sectors, 77
   industries.
 - Each standard defines: material topics, accounting metrics,
   activity metrics, technical protocols.
 - Now under ISSB (IFRS Foundation) — maintained as the
   "industry-based requirements" anchor of IFRS S1.
 - Example disclosure code: "SASB SV-PS-330a.3" (Software & IT
   Services, Recruitment of Foreign Talent).

**GRI (Global Reporting Initiative)**
 - Universal Standards 2021: GRI 1 (Foundation), GRI 2 (General
   Disclosures), GRI 3 (Material Topics).
 - Topic Standards: GRI 200 series (Economic), GRI 300 series
   (Environmental — 301-308), GRI 400 series (Social — 401-418).
 - Sector Standards (launched 2021): GRI 11 (Oil & Gas), GRI 12
   (Coal), GRI 13 (Agriculture/Aquaculture/Fishing), GRI 14
   (Mining) — more in development.
 - Example disclosure code: "GRI 305-1" (Direct Scope-1 GHG
   emissions).

**TCFD (Task Force on Climate-related Financial Disclosures)**
 - Four pillars: Governance, Strategy, Risk Management, Metrics &
   Targets.
 - 11 recommended disclosures.
 - Officially disbanded 2024; ISSB IFRS S2 took over. Still
   referenced as the conceptual baseline for climate disclosure.
 - Example: "TCFD Strategy-c" (resilience of strategy under
   different climate scenarios).

**ISSB IFRS S1 + S2**
 - IFRS S1 (General Requirements for Disclosure of
   Sustainability-related Financial Information) — January 2024.
 - IFRS S2 (Climate-related Disclosures) — January 2024.
 - 30+ jurisdictions adopting or planning to adopt as of 2026
   (UK, Japan, Australia, Canada, Singapore, Hong Kong, others).
 - EU CSRD ESRS interoperable with ISSB S1 + S2.

**SBTi (Science Based Targets initiative)**
 - Net-Zero Standard v1.2 (2024).
 - Categories: Near-term targets (5-10 yr), long-term targets
   (≤2050), corporate net-zero target, FLAG (Forest, Land,
   Agriculture).
 - Validation criteria — 1.5°C-aligned pathways (cross-sector
   ≥4.2%/yr Scope 1+2 reduction; SDA for power, cement, steel,
   transport, others).
 - Public list of validated companies + targets at
   sciencebasedtargets.org.

**Cross-walks:**
 - CSRD ESRS → SASB → ISSB S1 mapping (where they converge).
 - GRI Sector Standards → SASB Industry Standards (where they
   converge per industry).
 - TCFD → ISSB S2 (1:1 conceptual mapping; ISSB adds more
   detail).

Composite educational extracts. Authoritative versions at:
sasb.org, globalreporting.org, ifrs.org/issb, sciencebasedtargets.org.

**Industries**: esg, esg.csrd, sustainability, climate, compliance, cross_industry
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
| `data/esg-pillar-pack/sasb-industry-standards.jsonl` | jsonl | — |
| `data/esg-pillar-pack/gri-universal-and-topic-standards.jsonl` | jsonl | — |
| `data/esg-pillar-pack/tcfd-recommendations.jsonl` | jsonl | — |
| `data/esg-pillar-pack/issb-ifrs-s1-s2.jsonl` | jsonl | — |
| `data/esg-pillar-pack/sbti-net-zero-standard.jsonl` | jsonl | — |
| `data/esg-pillar-pack/framework-crosswalks.jsonl` | jsonl | — |

## Provenance

- **sources**: https://sasb.org/standards/, https://www.globalreporting.org/standards/, https://www.fsb-tcfd.org/recommendations/, https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/, https://sciencebasedtargets.org/standard
- **collected_through**: 2026-05-15

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/sasb-gri-tcfd-issb-standards.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{sasb-gri-tcfd-issb-standards_open_harness_hub,
  title  = {Voluntary sustainability disclosure frameworks — SASB / GRI / TCFD / ISSB / SBTi},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/sasb-gri-tcfd-issb-standards},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/sasb-gri-tcfd-issb-standards`.
