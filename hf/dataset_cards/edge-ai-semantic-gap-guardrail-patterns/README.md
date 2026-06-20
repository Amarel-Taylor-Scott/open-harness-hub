---
license: CC-BY-4.0
tags:
- ai
- classification
- cross_industry
- edge-ai
- encoding
- evaluation
- experimental
- guardrails
- media
- micro-model
- open-harness-hub
- routing
- safety_gating
- security.defensive
- semantic-gap
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Edge AI semantic gap guardrail patterns
---

# Edge AI semantic gap guardrail patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/edge-ai-semantic-gap-guardrail-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Reusable defensive patterns for encoded prompt detection, recursive sanitization, edge micro-model routing, and post-decode safety evaluation.

**Industries**: ai, security.defensive, media, cross_industry
**Capabilities**: safety_gating, classification, routing, evaluation
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `edge_ai_guardrail_pattern`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/edge-ai-semantic-gap-guardrail-patterns/patterns.jsonl` | jsonl | edge_ai_guardrail_pattern |

## Provenance

- **sources**: User-provided defensive architecture seed on encoded-payload semantic gaps, Open Harness Hub component design notes
- **collected_through**: 2026-05-26
- **collected_by**: Open Harness Hub contributors
- **anonymization**: Defensive summary only; no harmful operational payloads retained

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/edge-ai-semantic-gap-guardrail-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{edge-ai-semantic-gap-guardrail-patterns_open_harness_hub,
  title  = {Edge AI semantic gap guardrail patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/edge-ai-semantic-gap-guardrail-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/edge-ai-semantic-gap-guardrail-patterns`.
