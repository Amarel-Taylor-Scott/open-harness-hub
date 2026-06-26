---
name: disaster-assistance-multimodal-intake
description: Multi-model harness for disaster assistance intake that routes forms,
  narratives, damage images, geospatial incident boundaries, official rules, duplicate
  signals, and evidence gaps to reviewable eligibility packets.
when_to_use: Use when the user needs governance. Use when the user needs retrieval.
  Use when the user needs verification. Use when the user needs evaluation. Particularly
  relevant for humanitarian.disaster. Particularly relevant for government.benefits.
---

# Disaster assistance multimodal intake harness

Multi-model harness for disaster assistance intake that routes forms, narratives, damage images, geospatial incident boundaries, official rules, duplicate signals, and evidence gaps to reviewable eligibility packets.

## Applied layers

- `tools`
- `official_sources`
- `rag`
- `classifier`
- `privacy`

## Privacy boundaries

- **raw_input**: Applicant evidence can contain sensitive personal and location data; default to local processing or explicit tenant approval.
- **derived_output**: Eligibility packets require role-based access and redaction before analytics or publication.
- **external_calls**: Hosted vision or text models require explicit routing policy and redaction.

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `cheap_text_reasoner` | `openai_compatible` | mixed | False | True |
| `vision_damage_classifier` | `openai_compatible` | mixed | False | False |
| `local_guard_model` | `ollama` | local | False | False |

## Provenance

- Hub component: `harness/disaster-assistance-multimodal-intake` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
