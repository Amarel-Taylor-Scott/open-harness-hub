---
license: MIT
tags:
- cti
- evaluation
- experimental
- ioc
- mitre-attack
- open-harness-hub
- security
- synthetic
- threat_intelligence
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Synthetic threat-intelligence report samples
---

# Synthetic threat-intelligence report samples

<!-- Generated from Open Harness Hub manifest `dataset/threat-intel-samples` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Synthetic CTI report samples for testing
`pipeline/threat-intel-ioc-review`. Includes IOCs (file hashes,
IPs, domains, URLs, mutexes, CVEs, ATT&CK technique IDs, BTC
addresses) drawn from textbook examples — NOT real-world
indicators of compromise.

**Industries**: security, threat_intelligence
**Capabilities**: evaluation
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Provenance

- **origin**: Fully synthetic — IOCs are textbook examples, NOT live
- **collected_by**: Open Harness Hub contributors
- **collected_through**: 2026-05-20
- **license**: MIT
- **anonymization**: fully synthetic; no real adversary or victim data

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/threat-intel-samples.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{threat-intel-samples_open_harness_hub,
  title  = {Synthetic threat-intelligence report samples},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/dataset/threat-intel-samples},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `dataset/threat-intel-samples`.
