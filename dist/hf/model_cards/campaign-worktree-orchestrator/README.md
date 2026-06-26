---
license: MIT
tags:
- agentic-harness
- ai
- campaign-state
- cross_industry
- evaluation
- experimental
- governance
- multi-agent
- open-harness-hub
- orchestration
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

# Campaign worktree orchestrator

<!-- Generated from OpenHubForAI manifest `harness/campaign-worktree-orchestrator` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Harness pattern for coordinating multiple long-running coding agents across isolated worktrees with campaign state, worker queues, merge policy, retries, and audit logs.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `tools` layer
- `privacy` layer
- `heuristic` layer

**Industries**: ai, software.devops, cross_industry
**Capabilities**: governance, evaluation, serving
**Modalities**: text, structured
**Trust boundary**: mixed
## Privacy boundaries

- **raw_input**: Campaign state may include repo paths, logs, and operational traces; keep tenant-scoped.
- **derived_output**: Published summaries must omit secrets, private paths, and unreviewed user data.
- **external_calls**: External calls depend on configured worker adapters and must be declared per worker.

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
@misc{campaign-worktree-orchestrator_open_harness_hub,
  title  = {Campaign worktree orchestrator},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/campaign-worktree-orchestrator},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/campaign-worktree-orchestrator`.
