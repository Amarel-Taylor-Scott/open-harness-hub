---
name: water-quality-multimodal-triage
description: Multi-model harness for water quality triage that routes lab tables,
  sampling plans, chain-of-custody records, service-area maps, historical trends,
  official thresholds, and public notice drafts.
when_to_use: Use when the user needs governance. Use when the user needs retrieval.
  Use when the user needs verification. Use when the user needs evaluation. Particularly
  relevant for environmental.water. Particularly relevant for water_utility.sdwa.
---

# Water quality multimodal triage harness

Multi-model harness for water quality triage that routes lab tables, sampling plans, chain-of-custody records, service-area maps, historical trends, official thresholds, and public notice drafts.

## Applied layers

- `tools`
- `official_sources`
- `rag`
- `classifier`
- `privacy`

## Privacy boundaries

- **raw_input**: Operational utility data may be sensitive; keep raw tables and maps tenant-scoped.
- **derived_output**: Public notice drafts must pass legal and operator review before release.
- **external_calls**: Hosted drafting models receive only redacted, summarized findings unless explicitly approved.

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `tabular_threshold_checker` | `callable` | local | True | True |
| `notice_draft_model` | `openai_compatible` | mixed | False | False |
| `trend_summarizer` | `ollama` | local | False | False |

## Provenance

- Hub component: `harness/water-quality-multimodal-triage` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
