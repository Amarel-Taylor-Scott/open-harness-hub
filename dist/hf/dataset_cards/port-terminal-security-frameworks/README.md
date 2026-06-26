---
license: CC-BY-4.0
tags:
- expansion-v3
- experimental
- maritime.port_security
- open-harness-hub
- port-terminal-security
- retrieval
- security.defensive
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Port Terminal Security frameworks
---

# Port Terminal Security frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/port-terminal-security-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for port terminal security reviews, including evidence, escalation, and remediation controls.

**Industries**: maritime.port_security, security.defensive
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`
- `evidence_matrix`

## Files

| path | format | schema |
|---|---|---|
| `data/port-terminal-security/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Port Terminal Security control checklist, Port Terminal Security evidence matrix, Port Terminal Security escalation playbook, Port Terminal Security remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/port-terminal-security-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{port-terminal-security-frameworks_open_harness_hub,
  title  = {Port Terminal Security frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/port-terminal-security-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/port-terminal-security-frameworks`.
