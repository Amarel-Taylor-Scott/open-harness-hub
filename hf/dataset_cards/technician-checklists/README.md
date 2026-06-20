---
license: CC-BY-4.0
tags:
- aviation
- beta
- checklist
- compliance
- construction
- cyber
- energy
- esg
- finance
- food
- go-nogo
- healthcare
- human-performance
- infrastructure
- manufacturing
- mining
- nuclear
- open-harness-hub
- pharma
- procedural
- retrieval
- safety_gating
- telecommunications
- transportation
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Technician checklists — 50 industry procedural components
---

# Technician checklists — 50 industry procedural components

<!-- Generated from Open Harness Hub manifest `knowledge-pack/technician-checklists` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Canonical written checklists / standard work that real practitioners use: WHO Surgical Safety, FAA preflight, OSHA JHA, AORN counts, HACCP CCP, NFPA 70E LOTO, MSHA pre-shift, ITIL change, NIST 800-61 IR, KYC/CIP — 50 industries total with sources + steps + GO/NO-GO decisions.

**Industries**: compliance, healthcare, aviation, construction, energy, manufacturing, transportation, food, pharma, mining, infrastructure, telecommunications, nuclear, finance, cyber, esg
**Capabilities**: retrieval, verification, safety_gating
**Modalities**: text, structured
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/technician-checklists/checklists.jsonl` | jsonl | — |

## Provenance

- **sources**: WHO Guidelines for Safe Surgery 2009, 14 CFR 91 / 43 (FAA), OSHA 29 CFR 1910 + 1926 (multiple), AORN Guidelines for Perioperative Practice 2024, AWS D1.1/D1.1M:2020, ASNT SNT-TC-1A; ASME BPVC Sec V, NFPA 70E-2024; NFPA 85; NFPA 502, 21 CFR 1304/117/211 (DEA + FDA), Codex Alimentarius CXC 1-1969, ACR Appropriateness Criteria; CAP Cancer Protocols, USP <797>; EU GMP Annex 1, NBIC NB-23; ASME B30.5; ASME A17.1; ASHRAE Guideline 0/1.1, 30 CFR 75.360 (MSHA); 29 CFR 1910.119 (PSM), 23 CFR 650 (NBIS); 49 CFR 215/232/218/396 (FRA/FMCSA), 40 CFR 141 SDWA; 40 CFR 122/136 NPDES, ANSI/ASSP A10.48 (tower climb); INPO TQ-303, ITIL 4; NIST SP 800-61/800-115/800-184, PTES; OWASP WSTG v4.2; Google SRE Workbook, 31 CFR 1020/1010 (BSA/AML); PCAOB AS 2110; Treasury Circular 230, 12 CFR 1026 Reg Z; NAIC Model #900, GRI 1/2/3 (2021); Guide for the Care + Use of Lab Animals 8e (IACUC)
- **collected_through**: 2026-05-21
- **note**: Composite educational extracts — 50 procedural components. Each record carries source citation.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/technician-checklists.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{technician-checklists_open_harness_hub,
  title  = {Technician checklists — 50 industry procedural components},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/technician-checklists},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/technician-checklists`.
