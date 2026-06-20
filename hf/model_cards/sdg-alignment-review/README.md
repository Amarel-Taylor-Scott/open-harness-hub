---
license: MIT
tags:
- agenda-2030
- alignment
- classification
- esg
- evaluation
- experimental
- government
- harness
- humanitarian
- nonprofit
- open-harness-hub
- reasoning
- retrieval
- sdg
- structured
- sustainability
- text
- verification
library_name: open-harness-hub
pipeline_tag: text-classification
language:
- en
region:
- esg
- sustainability
- nonprofit
- government
- humanitarian
---

# UN SDG alignment-claim review harness

<!-- Generated from Open Harness Hub manifest `harness/sdg-alignment-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Wraps the SDG alignment-claim review flow as a reusable harness.
Classifies free-text claims to candidate SDG goals via the
classifier rule pack, drills to target/indicator level via RAG
against the SDG knowledge pack, checks counter-targets, and grades
alignment quality.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `classifier` layer
- `rag` layer
- `tools` layer

**Industries**: esg, sustainability, nonprofit, government, humanitarian
**Capabilities**: evaluation, verification, retrieval, classification, reasoning
**Modalities**: text, structured
**Trust boundary**: local

## How the harness runs

### claim text → candidate SDGs → target+indicator drilldown → counter-target check → grade

1. classify each claim into candidate SDG goals
2. RAG against SDG pack to identify exact targets + indicators
3. check counter-target risks via target-interactions matrix
4. assess additionality + geographic-temporal fit
5. judge per sdg-alignment-v1 rubric
6. propose strengthening edits per gap
7. emit audit trace

## Privacy boundaries

- **raw_input**: stays local
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
@misc{sdg-alignment-review_open_harness_hub,
  title  = {UN SDG alignment-claim review harness},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/sdg-alignment-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/sdg-alignment-review`.
