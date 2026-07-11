# Water quality multimodal triage harness

*harness* · `harness/water-quality-multimodal-triage` · v0.1.0 · experimental

Multi-model harness for water quality triage that routes lab tables, sampling plans, chain-of-custody records, service-area maps, historical trends, official thresholds, and public notice drafts.

| axis | value |
|---|---|
| industry | environmental.water, water_utility.sdwa |
| capability | governance, retrieval, verification, evaluation |
| modality | text, structured, tabular, spatial, timeseries, multimodal |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |

**Contributes to:** `pipeline/multimodal-public-service-harness-intake`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `tabular_threshold_checker` | `callable` | local | True | True |
| `notice_draft_model` | `openai_compatible` | mixed | False | False |
| `trend_summarizer` | `ollama` | local | False | False |

## Privacy boundaries

- **raw_input**: Operational utility data may be sensitive; keep raw tables and maps tenant-scoped.
- **derived_output**: Public notice drafts must pass legal and operator review before release.
- **external_calls**: Hosted drafting models receive only redacted, summarized findings unless explicitly approved.

