---
license: MIT
tags:
- beta
- compliance
- csddd
- esg
- evaluation
- harness
- open-harness-hub
- reasoning
- retrieval
- supply_chain
- text
- verification
library_name: open-harness-hub
pipeline_tag: text-generation
language:
- en
region:
- esg
- supply_chain
- compliance
---

# ESG Disclosure Grading harness

<!-- Generated from Open Harness Hub manifest `harness/esg-disclosure-grading` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Wraps the ESG supplier-policy-grading flow as a reusable harness
with persona + GREP + RAG + tools layers. Targets local-Ollama or
Anthropic/OpenAI for the judge model arm; emits citation-first
findings with CSDDD article + ILO indicator + national-law links.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `rag` layer
- `tools` layer

**Industries**: esg, supply_chain, compliance
**Capabilities**: evaluation, verification, retrieval, reasoning
**Modalities**: text
**Trust boundary**: local

## How the harness runs

### supplier-pack → red flags → CSDDD citations → grade + remediation

1. structured-to-prose normalize
2. redact PII per HIPAA Safe Harbor + DPV
3. fire S+E+G GREP packs
4. RAG against CSDDD + corridors + lead-company code
5. judge against esg-supplier-compliance rubric
6. propose Art-10 remediation with milestones
7. emit audit trace per CSDDD Art-26

## Privacy boundaries

- **raw_input**: stays local to the running pipeline
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
@misc{esg-disclosure-grading_open_harness_hub,
  title  = {ESG Disclosure Grading harness},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/esg-disclosure-grading},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/esg-disclosure-grading`.
