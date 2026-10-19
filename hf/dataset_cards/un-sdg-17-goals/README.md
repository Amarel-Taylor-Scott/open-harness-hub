---
license: CC-BY-4.0
tags:
- 5-ps
- agenda-2030
- cross_industry
- esg
- experimental
- government
- humanitarian
- indicators
- nonprofit
- open-harness-hub
- retrieval
- sdg
- sustainability
- targets
- un
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: UN Sustainable Development Goals (17 goals / 169 targets / 248 indicators)
---

# UN Sustainable Development Goals (17 goals / 169 targets / 248 indicators)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/un-sdg-17-goals` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Reference pack of (composite educational) extracts from the UN
2030 Agenda for Sustainable Development:

**The 17 Goals** (and their 5 Ps clustering):
 - **People** (1-5): No Poverty, Zero Hunger, Good Health & Well-
   being, Quality Education, Gender Equality.
 - **Planet** (6, 12-15): Clean Water & Sanitation, Responsible
   Consumption & Production, Climate Action, Life Below Water,
   Life on Land.
 - **Prosperity** (7-11): Affordable & Clean Energy, Decent Work
   & Economic Growth, Industry/Innovation/Infrastructure, Reduced
   Inequalities, Sustainable Cities & Communities.
 - **Peace** (16): Peace, Justice & Strong Institutions.
 - **Partnership** (17): Partnerships for the Goals.

**169 Targets** — the operational sub-goals (e.g., Target 1.1
"By 2030, eradicate extreme poverty for all people everywhere,
currently measured as people living on less than $2.15 a day").

**248 Indicators** — Global Indicator Framework (E/CN.3/2025/2,
2025 refinement). 231 unique indicators with multiple appearances;
tier classification (Tier I = methodology + data both ready,
Tier II = methodology ready / data sparse, Tier III =
methodology under development).

**Target-interaction matrix**: synergies (one target's progress
helps another) and trade-offs (one target's progress can harm
another). Examples:
 - 7 (energy) ↔ 13 (climate): strong synergy via renewables.
 - 7 (energy) ↔ 15 (life on land): trade-off via lithium / cobalt
   mining and dam-flooding.
 - 2 (hunger) ↔ 15 (life on land): trade-off via agricultural
   intensification.
 - 8 (growth) ↔ 10 (inequality): often-noted trade-off when
   growth is unevenly distributed.
 - 9 (infrastructure) ↔ 13 (climate): trade-off via concrete /
   steel emissions; synergy via resilient infrastructure.
 - 14 (oceans) ↔ 2 (hunger): trade-off via overfishing for food
   security.

**Progress reality (per UN SDG Report 2025):**
 - Only ~17% of targets are on track.
 - 39 targets show moderate progress.
 - 18 targets show insufficient progress.
 - 36 targets show stagnation or regression.
 - 4 years left in "Decade of Action."

**CSRD ESRS / GRI / SASB cross-walks** to SDG (optional mappings
published by each framework).

**Common SDG-washing patterns:**
 - Goal-level claim without target-level backing.
 - Counter-target ignorance.
 - Geographic / temporal mismatch.
 - Additionality unverified.
 - Indicator misuse (using a custom KPI under a UN-indicator label).

Composite educational extracts. Authoritative source:
sdgs.un.org/goals + UN Statistical Commission Global Indicator
Framework documents.

**Industries**: esg, sustainability, nonprofit, government, humanitarian, cross_industry
**Capabilities**: retrieval, verification
**Modalities**: text, structured
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `citation_edge`

## Files

| path | format | schema |
|---|---|---|
| `data/sdg-pack/goals-and-targets.jsonl` | jsonl | — |
| `data/sdg-pack/global-indicator-framework-2025.jsonl` | jsonl | — |
| `data/sdg-pack/target-interactions-matrix.jsonl` | jsonl | — |
| `data/sdg-pack/sdg-report-2025-progress.jsonl` | jsonl | — |
| `data/sdg-pack/framework-crosswalks.jsonl` | jsonl | — |

## Provenance

- **sources**: https://sdgs.un.org/goals, https://unstats.un.org/sdgs/indicators/indicators-list/, UN SDG Report 2025 (E/2025/56), Global Indicator Framework refinement E/CN.3/2025/2, UN-DESA SDG interactions matrix (2023)
- **collected_through**: 2026-05-15

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/un-sdg-17-goals.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{un-sdg-17-goals_open_harness_hub,
  title  = {UN Sustainable Development Goals (17 goals / 169 targets / 248 indicators)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/un-sdg-17-goals},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/un-sdg-17-goals`.
