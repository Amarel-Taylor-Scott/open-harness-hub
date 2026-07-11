---
license: MIT
tags:
- cross_industry
- delegation
- experimental
- open-harness-hub
- personal-assistant
- personal_productivity
- privacy
- retrieval
- user-preferences
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: User preference schema (canonical shape for personal assistants)
---

# User preference schema (canonical shape for personal assistants)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/user-preference-schema` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Canonical schema for storing user preferences that personal-
assistant harnesses load before taking action. Covers:
 - Communication tone preferences (formal / casual / terse / warm)
 - Scheduling rules (no-meeting hours, focus blocks, time-zone)
 - Privacy rules (what is shareable with whom)
 - Delegation rules (who can act on user's behalf for what)
 - Tool autonomy (autonomous / review-required / never)
 - Recurring tasks + commitments

The schema is portable — same shape works across email / chat /
calendar / personal-RAG harnesses.

**Industries**: personal_productivity, cross_industry
**Capabilities**: retrieval
**Modalities**: text, structured
**Freshness**: volatile
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/personal-assistant-pack/preference-schema-and-defaults.jsonl` | jsonl | — |

## Provenance

- **sources**: Composite of common personal-assistant preference patterns
- **collected_through**: 2026-05-20
- **note**: Schema + recommended defaults. Real instances replace defaults with user-specific values.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/user-preference-schema.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{user-preference-schema_open_harness_hub,
  title  = {User preference schema (canonical shape for personal assistants)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/user-preference-schema},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `knowledge-pack/user-preference-schema`.
