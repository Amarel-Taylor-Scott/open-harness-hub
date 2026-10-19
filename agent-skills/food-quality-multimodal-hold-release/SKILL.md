---
name: food-quality-multimodal-hold-release
description: Multi-model harness for food quality and safety triage that routes product
  photos, label OCR, lot codes, temperature logs, supplier records, complaint narratives,
  inspection notes, and recall or hold-release rules.
when_to_use: Use when the user needs governance. Use when the user needs retrieval.
  Use when the user needs verification. Use when the user needs evaluation. Particularly
  relevant for food.safety. Particularly relevant for food_safety. Particularly relevant
  for logistics.cold_chain.
---

# Food quality multimodal hold-release harness

Multi-model harness for food quality and safety triage that routes product photos, label OCR, lot codes, temperature logs, supplier records, complaint narratives, inspection notes, and recall or hold-release rules.

## Applied layers

- `tools`
- `official_sources`
- `rag`
- `classifier`
- `privacy`

## Privacy boundaries

- **raw_input**: Supplier records and complaint details remain tenant-scoped.
- **derived_output**: Disposition packets may contain commercially sensitive data and require review before sharing.
- **external_calls**: Hosted OCR or vision models require redaction and approved routing.

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `label_ocr_model` | `openai_compatible` | mixed | False | False |
| `temperature_log_checker` | `callable` | local | True | True |
| `quality_disposition_model` | `ollama` | local | False | True |

## Provenance

- Hub component: `harness/food-quality-multimodal-hold-release` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
