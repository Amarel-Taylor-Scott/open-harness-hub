---
license: MIT
tags:
- beta
- evaluation
- fleischner
- harness
- healthcare
- healthcare.radiology
- hipaa
- open-harness-hub
- radiology
- rads
- reasoning
- retrieval
- text
- verification
library_name: open-harness-hub
pipeline_tag: text-generation
language:
- en
region:
- healthcare
- healthcare.radiology
---

# Radiology Report Review harness

<!-- Generated from OpenHubForAI manifest `harness/radiology-report-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

RADS-aware + Fleischner-aware harness for grading radiology reports
with HIPAA-safe PHI redaction. Wraps `pipeline/radiology-report-
grading` with reusable layers.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `privacy` layer
- `grep` layer
- `rag` layer
- `tools` layer

**Industries**: healthcare, healthcare.radiology
**Capabilities**: evaluation, verification, retrieval, reasoning
**Modalities**: text
**Trust boundary**: local

## How the harness runs

### structured report → PHI-redact → RADS+Fleischner heuristics → grade

1. structured-to-prose
2. rule-pack/phi-hipaa-en redaction
3. radiology-report-red-flags GREP
4. RAG against ACR Appropriateness Criteria + Fleischner 2017 + RADS
5. judge against radiology-report-quality rubric
6. audit trace

## Privacy boundaries

- **raw_input**: stays local; PHI redacted
- **derived_output**: may sync to hub only after anonymization gate
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `local_ollama` | `ollama` | local |
| `anthropic_judge` | `anthropic` | external |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{radiology-report-review_open_harness_hub,
  title  = {Radiology Report Review harness},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/radiology-report-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/radiology-report-review`.
