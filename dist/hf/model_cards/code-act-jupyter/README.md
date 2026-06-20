---
license: MIT
tags:
- ai
- beta
- code
- code-act
- code_execution
- education
- jupyter
- kaggle-verified
- open-harness-hub
- reasoning
- scientific_research
- text
- tool-use
- tool_use
library_name: open-harness-hub
pipeline_tag: text-generation
language:
- en
region:
- ai
- scientific_research
- education
---

# Code-Act Jupyter (tool-augmented reasoning via sandboxed Python)

<!-- Generated from Open Harness Hub manifest `harness/code-act-jupyter` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Harness that wraps a model call with a Python execution loop. The
model emits `<code>...</code>` blocks; the harness runs them in a
sandboxed Jupyter kernel; stdout / stderr / repr feed back into the
next turn. Loop terminates when the model emits a `<final>...
</final>` block or `max_tool_turns` is reached.

The classic AIMO-2 + ChartQA + math-reasoning shape, verified by
Open Harness Hub mining: itahiro DeepSeek-R1-distill-7B (1399
votes), lewtun "Updated Code Interpretation" (1173), abdurrafae
(1001), mbmmurad QwQ-32B (1097).

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `tools` layer

**Industries**: ai, scientific_research, education
**Capabilities**: reasoning, tool_use, code_execution
**Modalities**: text, code
**Trust boundary**: local

## How the harness runs

### Prompt → code → execute → observe → repeat

1. compose persona + task
2. call model
3. extract <code>...</code> blocks
4. execute in sandbox kernel
5. feed observation back as user turn
6. stop on <final>...</final> or max_turns

## Privacy boundaries

- **raw_input**: stays local to the kernel process
- **derived_output**: transcript may be synced post-anonymization
- **external_calls**: kernel network egress is off by default

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `local_vllm` | `vllm` | local |
| `local_ollama` | `ollama` | local |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{code-act-jupyter_open_harness_hub,
  title  = {Code-Act Jupyter (tool-augmented reasoning via sandboxed Python)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/code-act-jupyter},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub artifact: `harness/code-act-jupyter`.
