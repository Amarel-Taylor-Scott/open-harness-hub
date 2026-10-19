---
license: MIT
tags:
- creative
- cross_industry
- evaluation
- experimental
- extraction
- harness
- launch
- open-harness-hub
- product-hunt
- reasoning
- saas
- software
- text
library_name: open-harness-hub
pipeline_tag: token-classification
language:
- en
region:
- software
- creative
- cross_industry
---

# SaaS launch landing-page review harness

<!-- Generated from Open Harness Hub manifest `harness/saas-launch-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Wraps the SaaS launch review flow as a reusable harness. Reviews
landing-page copy + tagline + pricing + demo materials against
corpus norms and anti-pattern rules; produces per-aspect findings
with severity, observation, corpus norm, and suggested rewrite.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `rag` layer
- `tools` layer

**Industries**: software, creative, cross_industry
**Capabilities**: evaluation, extraction, reasoning
**Modalities**: text
**Trust boundary**: local

## How the harness runs

### landing page → anti-pattern flags → corpus-norm RAG → per-aspect grade + rewrites

1. extract tagline + ICP + feature list + pricing + demo info
2. fire SaaS-launch anti-pattern GREP pack
3. RAG against SaaS launch best-practices pack per aspect
4. judge per saas-launch-quality-v1 rubric
5. propose per-finding rewrites
6. emit audit trace

## Privacy boundaries

- **raw_input**: stays local; landing-page text is public
- **derived_output**: may sync to hub
- **external_calls**: only on explicit user opt-in

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
@misc{saas-launch-review_open_harness_hub,
  title  = {SaaS launch landing-page review harness},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/saas-launch-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/saas-launch-review`.
