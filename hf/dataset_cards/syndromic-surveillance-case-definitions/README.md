---
license: CC-BY-4.0
tags:
- africa
- afyaedge
- beta
- classification
- cross_industry
- defensive
- ewarn
- field-epidemiology
- global-south
- government.regulatory
- healthcare.public_health
- idsr
- offline
- on-device
- open-harness-hub
- outbreak-threshold
- public_safety
- retrieval
- safety
- structural-lift
- syndromic-surveillance
- who
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: WHO syndromic surveillance case definitions and outbreak thresholds (offline)
---

# WHO syndromic surveillance case definitions and outbreak thresholds (offline)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/syndromic-surveillance-case-definitions` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Offline Knowledge Corpus of public-domain WHO syndromic surveillance case
definitions covering: acute watery diarrhoea (cholera), acute respiratory
illness (ARI/ILI), meningitis syndrome, acute haemorrhagic fever, acute
jaundice, severe acute malnutrition (SAM), and measles-like rash illness.
Each entry includes the WHO IDSR (Integrated Disease Surveillance and
Response) or EWARN alert threshold, the minimum case definition criteria,
and the escalation tier (Green/Yellow/Red) used by the AfyaEdge triage
pattern.

DEFENSIVE INGESTION CONTRACT:
- All content sourced from public-domain WHO IDSR 3rd edition and WHO
  EWARN field guides; no novel clinical criteria are generated.
- This corpus is a decision-SUPPORT reference only. It does NOT replace
  clinical diagnosis or official epidemiological investigation.
- Every harness consuming this pack MUST surface the disclaimer:
  "These are surveillance thresholds for triage support only — always
  confirm with a trained health officer and escalate to MoH as required."
- Alert thresholds may be superseded by in-country MoH guidance; treat
  this corpus as a baseline pending local calibration.
- Volatile facts (active outbreak status, local MoH contacts) are
  excluded; only stable syndromic definitions and baseline thresholds
  are included.

CAPABILITY LIFT (structural): in remote/low-resource community health
settings, network connectivity is absent or unreliable. Field health
workers cannot query WHO servers mid-consultation. This corpus encodes
the stable syndromic decision rules so the on-device triage assistant
can function when cloud retrieval is impossible.
lift_reason: no_addressable_source (network unavailable in the field);
mechanism: context_length (no model can reliably recall all IDSR
thresholds at inference time without retrieval).

**Industries**: healthcare.public_health, public_safety, government.regulatory, cross_industry
**Capabilities**: retrieval, safety, classification
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `citation_edge`

## Files

| path | format | schema |
|---|---|---|
| `data/syndromic-surveillance-case-definitions.jsonl` | jsonl | — |

## Provenance

- **sources**: WHO Integrated Disease Surveillance and Response (IDSR) Technical Guidelines, 3rd edition (2020) — public domain, CC-BY-NC-SA-3.0-IGO, WHO EWARN (Early Warning Alert and Response Network) Field Guide — public domain, WHO Communicable Disease Toolkit for Syria (community health syndromic definitions section) — public domain
- **collected_through**: 2026-05-28
- **collected_by**: Open Harness Hub research agent (manual curation from public-domain WHO sources)
- **anonymization**: none — all content is public-domain reference material; no PII

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/syndromic-surveillance-case-definitions.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{syndromic-surveillance-case-definitions_open_harness_hub,
  title  = {WHO syndromic surveillance case definitions and outbreak thresholds (offline)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/syndromic-surveillance-case-definitions},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/syndromic-surveillance-case-definitions`.
