---
license: CC-BY-4.0
tags:
- ai
- alert-review
- checklists
- cross_industry
- evaluation
- experimental
- finance.aml
- governance
- healthcare.public_health
- open-harness-hub
- procedure-objects
- questions
- retrieval
- verification
- versioned-facts
- wayback
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Procedure knowledge object patterns
---

# Procedure knowledge object patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/procedure-knowledge-object-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Reusable patterns for turning checklists, review questions, decision gates, evidence requirements, escalation rules, and versioned facts into indexed RAG objects.

**Industries**: ai, finance.aml, healthcare.public_health, cross_industry
**Capabilities**: retrieval, verification, governance, evaluation
**Modalities**: text, structured
**Freshness**: volatile
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `review_question`
- `checklist_item`
- `decision_gate`
- `evidence_requirement`
- `typology_mapping`
- `narrative_template`
- `versioned_fact`

## Files

| path | format | schema |
|---|---|---|
| `data/procedure-knowledge-object-patterns/patterns.jsonl` | jsonl | — |

## Provenance

- **sources**: OpenHubForAI procedure knowledge object architecture
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: synthetic procedure patterns only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/procedure-knowledge-object-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{procedure-knowledge-object-patterns_open_harness_hub,
  title  = {Procedure knowledge object patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/procedure-knowledge-object-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/procedure-knowledge-object-patterns`.
