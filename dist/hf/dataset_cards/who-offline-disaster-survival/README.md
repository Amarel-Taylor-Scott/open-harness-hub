---
license: CC-BY-4.0
tags:
- beta
- cpr
- cross_industry
- defensive
- disaster
- earthquake
- emergency
- fire
- first-aid
- flood
- healthcare.public_health
- ifrc
- offline
- on-device
- open-harness-hub
- public_safety
- public_safety.ems
- retrieval
- safety
- structural-lift
- who
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: WHO-aligned offline disaster survival and first-aid protocols
---

# WHO-aligned offline disaster survival and first-aid protocols

<!-- Generated from OpenHubForAI manifest `knowledge-pack/who-offline-disaster-survival` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Offline Knowledge Corpus of public-domain first-aid and disaster survival
protocols covering: floods, fires, earthquakes, cardiac arrest (CPR),
choking, severe bleeding, burns, and fracture management. Content is
structured from publicly available WHO Basic Emergency Care (BEC) guidelines
and IFRC First Aid materials. Each entry is cited to a source section so
the emergency-survival-guide persona can surface verbatim citations.

DEFENSIVE INGESTION CONTRACT:
- Content is sourced exclusively from public-domain WHO and IFRC materials.
- No novel medical instructions are generated; all steps are source-cited.
- This corpus is a reference only. It does not replace professional
  medical care or emergency services. Every harness consuming this pack
  MUST surface the disclaimer: "This is guidance only — call emergency
  services immediately if possible."
- Volatile facts (e.g., local emergency numbers) are excluded; only
  stable procedural protocols are included.

CAPABILITY LIFT (structural): network is structurally absent during
disasters — this corpus enables the persona/emergency-survival-guide to
function when cloud retrieval is impossible. The authoritative procedural
content (WHO BEC) is stable and can be fully cached on-device.
lift_reason: no_addressable_source (network unavailable in disaster).

**Industries**: healthcare.public_health, public_safety, public_safety.ems, cross_industry
**Capabilities**: retrieval, safety
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `citation_edge`

## Files

| path | format | schema |
|---|---|---|
| `data/who-offline-disaster-survival.jsonl` | jsonl | — |

## Provenance

- **sources**: WHO Basic Emergency Care: approach to the acutely ill and injured (2nd ed., 2024) — public domain, CC-BY-NC-SA-3.0-IGO, IFRC First Aid 2020 Guidelines — public domain summary chapters
- **collected_through**: 2026-05-28
- **collected_by**: OpenHubForAI research agent (manual curation from public-domain sources)
- **anonymization**: none — all content is public-domain reference material; no PII

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/who-offline-disaster-survival.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{who-offline-disaster-survival_open_harness_hub,
  title  = {WHO-aligned offline disaster survival and first-aid protocols},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/who-offline-disaster-survival},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/who-offline-disaster-survival`.
