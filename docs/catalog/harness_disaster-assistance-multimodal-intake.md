# Disaster assistance multimodal intake harness

*harness* · `harness/disaster-assistance-multimodal-intake` · v0.1.0 · experimental

Multi-model harness for disaster assistance intake that routes forms, narratives, damage images, geospatial incident boundaries, official rules, duplicate signals, and evidence gaps to reviewable eligibility packets.

| axis | value |
|---|---|
| industry | humanitarian.disaster, government.benefits |
| capability | governance, retrieval, verification, evaluation |
| modality | text, image, structured, spatial, multimodal |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |

**Contributes to:** `pipeline/multimodal-public-service-harness-intake`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `cheap_text_reasoner` | `openai_compatible` | mixed | False | True |
| `vision_damage_classifier` | `openai_compatible` | mixed | False | False |
| `local_guard_model` | `ollama` | local | False | False |

## Privacy boundaries

- **raw_input**: Applicant evidence can contain sensitive personal and location data; default to local processing or explicit tenant approval.
- **derived_output**: Eligibility packets require role-based access and redaction before analytics or publication.
- **external_calls**: Hosted vision or text models require explicit routing policy and redaction.

