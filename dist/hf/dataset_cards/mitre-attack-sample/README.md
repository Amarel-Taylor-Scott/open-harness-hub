---
license: CC-BY-4.0
tags:
- attack
- beta
- classification
- mitre
- open-harness-hub
- retrieval
- security
- threat-intel
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: MITRE ATT&CK techniques (sample)
---

# MITRE ATT&CK techniques (sample)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/mitre-attack-sample` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Sample of MITRE ATT&CK Enterprise tactics + techniques. Each row
carries the technique ID, name, tactic, and a one-paragraph
description. Use the canonical MITRE source at attack.mitre.org for
production — this is a 30-row sample illustrating the row shape.

**Industries**: security
**Capabilities**: retrieval, classification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/mitre-attack-sample.jsonl` | jsonl | — |

## Provenance

- **sources**: MITRE ATT&CK Enterprise v15 (https://attack.mitre.org/)
- **collected_through**: 2026-04-30

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/mitre-attack-sample.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{mitre-attack-sample_open_harness_hub,
  title  = {MITRE ATT&CK techniques (sample)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/mitre-attack-sample},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub artifact: `knowledge-pack/mitre-attack-sample`.
