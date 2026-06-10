---
license: CC-BY-4.0
tags:
- beta
- compliance
- cross_industry
- csddd
- esg
- ilo
- lksg
- modern-slavery
- open-harness-hub
- retrieval
- sb-657
- supply-chain
- supply_chain
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Global supply-chain due-diligence regulatory pack
---

# Global supply-chain due-diligence regulatory pack

<!-- Generated from Open Harness Hub manifest `knowledge-pack/csddd-and-forced-labor-indicators` v0.2.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Reference pack of (composite, educational) extracts from 12
jurisdictions + 4 international frameworks:

**EU:**
 - CSDDD (Directive 2024/1760) — Arts. 5 (risk-based DD), 7
   (integration), 10 (remediation), 11 (grievance), 13 (climate
   transition plan), 14 (monitoring), 17 (substantiated concerns),
   18 (mediation), 22 (supervisory authorities), 26 (board
   oversight), 27 (civil liability).
 - CSRD (Directive 2022/2464) — ESRS S1/S2 (own workforce + value
   chain workers), E1-E5 (environmental).
 - EU Deforestation Regulation (Reg. 2023/1115).
 - Conflict Minerals Regulation (Reg. 2017/821).

**National (Europe):**
 - UK Modern Slavery Act 2015 §54.
 - Germany LkSG (Lieferkettensorgfaltspflichtengesetz, 2021).
 - France Loi sur le Devoir de Vigilance (2017).
 - Norway Transparency Act (Åpenhetsloven, 2022).
 - Switzerland Code of Obligations Art. 964j (RBI ordinance).
 - Netherlands Child Labour Due Diligence Law.

**National (North America / APAC):**
 - California SB 657 (Transparency in Supply Chains, 2010).
 - US Uyghur Forced Labor Prevention Act (UFLPA, 2021).
 - US Tariff Act §307 + CBP Withhold Release Orders.
 - Canada Bill S-211 (Fighting Against Forced Labour, 2024).
 - Australia Modern Slavery Act (2018).
 - Japan Guidelines on Respecting Human Rights (METI, 2022).

**International frameworks:**
 - ILO 11 forced-labor indicators (Hard to See, Harder to Count, 2012).
 - UN Guiding Principles on Business & Human Rights (Ruggie, 2011).
 - OECD MNE Guidelines (2023 update).
 - OECD Due Diligence Guidance for Responsible Business Conduct.
 - ETI Base Code (Ethical Trading Initiative).

Designed as a citation backbone for `pipeline/supplier-policy-grading`
and downstream ESG audit pipelines. Composite educational extracts;
not authoritative legal text.

**Industries**: esg, supply_chain, compliance, cross_industry
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
| `data/csddd-pack/csddd-articles.jsonl` | jsonl | — |
| `data/csddd-pack/csrd-esrs.jsonl` | jsonl | — |
| `data/csddd-pack/ilo-forced-labor-indicators.jsonl` | jsonl | — |
| `data/csddd-pack/national-laws-summary.jsonl` | jsonl | — |
| `data/csddd-pack/international-frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: EU Directive 2024/1760 (CSDDD), composite extracts, EU Directive 2022/2464 (CSRD ESRS), composite extracts, EU Regulation 2023/1115 (Deforestation), composite extracts, EU Regulation 2017/821 (Conflict Minerals), composite extracts, ILO Hard to See, Harder to Count (2012), composite extracts, UK Modern Slavery Act 2015 §54, composite extracts, Germany LkSG (2021), composite extracts, France Loi sur le Devoir de Vigilance (2017), composite extracts, Norway Åpenhetsloven (2022), composite extracts, Switzerland Code of Obligations Art. 964j, composite extracts, Netherlands Child Labour Due Diligence Law, composite extracts, California SB 657 (2010), composite extracts, US UFLPA (2021), composite extracts, US CBP Withhold Release Orders + Findings list (snapshot 2026-04-30), Canada Bill S-211 (2024), composite extracts, Australia Modern Slavery Act (2018), composite extracts, Japan METI Guidelines (2022), composite extracts, UN Guiding Principles (Ruggie 2011), composite extracts, OECD MNE Guidelines (2023), composite extracts, OECD Due Diligence Guidance (2018), composite extracts, ETI Base Code, composite extracts
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts; not authoritative legal text.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/csddd-and-forced-labor-indicators.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{csddd-and-forced-labor-indicators_open_harness_hub,
  title  = {Global supply-chain due-diligence regulatory pack},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/csddd-and-forced-labor-indicators},
  version= {0.2.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub artifact: `knowledge-pack/csddd-and-forced-labor-indicators`.
