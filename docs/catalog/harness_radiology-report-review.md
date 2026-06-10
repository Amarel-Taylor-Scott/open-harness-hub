# Radiology Report Review harness

*harness* · `harness/radiology-report-review` · v0.1.0 · beta

RADS-aware + Fleischner-aware harness for grading radiology reports
with HIPAA-safe PHI redaction. Wraps `pipeline/radiology-report-
grading` with reusable layers.

| axis | value |
|---|---|
| industry | healthcare, healthcare.radiology |
| capability | evaluation, verification, retrieval, reasoning |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**Emits:** `reasoning_step`, `context_snippet`

**Contributes to:** `pipeline/radiology-report-grading`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Logic paths

### structured report → PHI-redact → RADS+Fleischner heuristics → grade  
*model_call: `required`*

1. structured-to-prose
1. rule-pack/phi-hipaa-en redaction
1. radiology-report-red-flags GREP
1. RAG against ACR Appropriateness Criteria + Fleischner 2017 + RADS
1. judge against radiology-report-quality rubric
1. audit trace

**consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**emits:** `reasoning_step`, `context_snippet`

**verification:** report structure present (history/technique/comparison/findings/impression/recommendation), zero PHI in graded output, RADS score on every applicable finding, Fleischner-compliant follow-up on incidental pulm nodules



## Privacy boundaries

- **raw_input**: stays local; PHI redacted
- **derived_output**: may sync to hub only after anonymization gate
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

