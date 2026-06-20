---
license: MIT
tags:
- agentic-harness
- ai
- cross_industry
- evaluation
- experimental
- governance
- harness-evolution
- meta-harness
- open-harness-hub
- serving
- software.devops
- structured
- text
- worktree
library_name: open-harness-hub
language:
- en
region:
- ai
- software.devops
- cross_industry
---

# Meta-harness evolver

<!-- Generated from Open Harness Hub manifest `harness/meta-harness-evolver` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Harness pattern that proposes, benchmarks, compares, and safely updates other harnesses using isolated branches, rollback paths, and human review gates.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `tools` layer
- `privacy` layer
- `heuristic` layer
- `classifier` layer

**Industries**: ai, software.devops, cross_industry
**Capabilities**: governance, evaluation, serving
**Modalities**: text, structured
**Trust boundary**: mixed
## Privacy boundaries

- **raw_input**: Harness traces may include sensitive repo and run context; keep local or tenant-scoped.
- **derived_output**: Publish only reviewed benchmark deltas and sanitized proposal summaries.
- **external_calls**: External calls depend on configured proposer and evaluator adapters.

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `none` | `none` | local |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{meta-harness-evolver_open_harness_hub,
  title  = {Meta-harness evolver},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/meta-harness-evolver},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/meta-harness-evolver`.
