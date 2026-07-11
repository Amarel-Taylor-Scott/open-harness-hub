---
license: CC-BY-4.0
tags:
- ai
- cross_industry
- experimental
- governance
- government
- identity
- open-harness-hub
- personal-rag
- planning
- provenance
- rag-network
- retrieval
- revocation
- signed-knowledge
- software.devops
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Signed knowledge network patterns
---

# Signed knowledge network patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/signed-knowledge-network-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Patterns for signed personal, organizational, government, and project knowledge objects that can be verified, indexed, embedded, revoked, and safely used in RAG and LLM pipelines.

**Industries**: ai, software.devops, government, cross_industry
**Capabilities**: verification, governance, retrieval, planning
**Modalities**: text, structured
**Freshness**: volatile
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `signed_knowledge_object`
- `publisher_identity`
- `usage_policy`
- `revocation_record`
- `trust_level`

## Files

| path | format | schema |
|---|---|---|
| `data/signed-knowledge-network-patterns/patterns.jsonl` | jsonl | — |

## Provenance

- **sources**: OpenHubForAI signed knowledge network architecture
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: synthetic architecture patterns only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/signed-knowledge-network-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{signed-knowledge-network-patterns_open_harness_hub,
  title  = {Signed knowledge network patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/signed-knowledge-network-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/signed-knowledge-network-patterns`.
