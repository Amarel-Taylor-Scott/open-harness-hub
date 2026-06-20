---
license: MIT
tags:
- differential-diagnosis
- experimental
- healthcare
- healthcare.clinical
- open-harness-hub
- phi-safe
- reasoning
- retrieval
- safety_gating
- text
- tool_use
library_name: open-harness-hub
pipeline_tag: text-generation
language:
- en
region:
- healthcare
- healthcare.clinical
---

# Clinical Decision Support

<!-- Generated from Open Harness Hub manifest `harness/clinical-decision-support` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Healthcare-specific harness for differential-diagnosis reasoning.
Composes the clinical-reasoner persona, red-flag classifier rules,
HIPAA PHI privacy gate, clinical-guideline RAG, ICD-10 lookup tool,
and a citation-first response policy. Educational / decision-
support framing; never a substitute for a licensed clinician.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `classifier` layer
- `rag` layer
- `tools` layer
- `privacy` layer

**Industries**: healthcare, healthcare.clinical
**Capabilities**: reasoning, retrieval, safety_gating, tool_use
**Modalities**: text
**Trust boundary**: local

## How the harness runs

### Differential diagnosis with red-flag escalation

1. redact PHI (rule-pack/phi-hipaa-en)
2. fire red-flag classifier (rule-pack/clinical-red-flags)
3. if any red flag fires → first sentence states the flag + recommend immediate evaluation
4. retrieve guideline chunks (knowledge-pack/clinical-guidelines-sample)
5. expand chunks with 1-hop citation graph
6. call ICD-10 lookup tool for code candidates
7. compose persona + retrieved chunks + tool results
8. call model
9. verify every claim cited by guideline section
10. produce ranked differential with prior probabilities

## Privacy boundaries

- **raw_input**: stays local; never sent to external API by default
- **derived_output**: stays local; only sharable after explicit user opt-in AND PHI re-scan
- **external_calls**: none by default; external judges require user opt-in
- **hipaa_safe_harbor**: applies — 18 identifier categories are redacted on input

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `local_ollama` | `ollama` | local |
| `self_hosted_gpu` | `transformers` | local |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{clinical-decision-support_open_harness_hub,
  title  = {Clinical Decision Support},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/clinical-decision-support},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub artifact: `harness/clinical-decision-support`.
