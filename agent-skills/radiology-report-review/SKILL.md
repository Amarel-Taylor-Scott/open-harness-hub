---
name: radiology-report-review
description: RADS-aware + Fleischner-aware harness for grading radiology reports with
  HIPAA-safe PHI redaction. Wraps `pipeline/radiology-report- grading` with reusable
  layers.
when_to_use: Use when the user needs evaluation. Use when the user needs verification.
  Use when the user needs retrieval. Use when the user needs reasoning. Particularly
  relevant for healthcare. Particularly relevant for healthcare.radiology.
---

# Radiology Report Review harness

RADS-aware + Fleischner-aware harness for grading radiology reports
with HIPAA-safe PHI redaction. Wraps `pipeline/radiology-report-
grading` with reusable layers.

## Applied layers

- `persona`
- `privacy`
- `grep`
- `rag`
- `tools`

## structured report → PHI-redact → RADS+Fleischner heuristics → grade

*model_call:* `required`

**Steps**

1. structured-to-prose
2. rule-pack/phi-hipaa-en redaction
3. radiology-report-red-flags GREP
4. RAG against ACR Appropriateness Criteria + Fleischner 2017 + RADS
5. judge against radiology-report-quality rubric
6. audit trace

**Verification**

- report structure present (history/technique/comparison/findings/impression/recommendation)
- zero PHI in graded output
- RADS score on every applicable finding
- Fleischner-compliant follow-up on incidental pulm nodules

## Privacy boundaries

- **raw_input**: stays local; PHI redacted
- **derived_output**: may sync to hub only after anonymization gate
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Provenance

- Hub component: `harness/radiology-report-review` v0.1.0
- License: `MIT`
- Lifecycle: `beta`
- Full source manifest: see `references/manifest.yaml`
