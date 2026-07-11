# Food quality multimodal hold-release harness

*harness* · `harness/food-quality-multimodal-hold-release` · v0.1.0 · experimental

Multi-model harness for food quality and safety triage that routes product photos, label OCR, lot codes, temperature logs, supplier records, complaint narratives, inspection notes, and recall or hold-release rules.

| axis | value |
|---|---|
| industry | food.safety, food_safety, logistics.cold_chain |
| capability | governance, retrieval, verification, evaluation |
| modality | text, image, structured, tabular, timeseries, multimodal |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |

**Contributes to:** `pipeline/multimodal-public-service-harness-intake`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `label_ocr_model` | `openai_compatible` | mixed | False | False |
| `temperature_log_checker` | `callable` | local | True | True |
| `quality_disposition_model` | `ollama` | local | False | True |

## Privacy boundaries

- **raw_input**: Supplier records and complaint details remain tenant-scoped.
- **derived_output**: Disposition packets may contain commercially sensitive data and require review before sharing.
- **external_calls**: Hosted OCR or vision models require redaction and approved routing.

