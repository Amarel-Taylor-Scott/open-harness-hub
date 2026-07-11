---
license: MIT
tags:
- chat
- cross_industry
- dialogue
- experimental
- memory
- multi-turn
- open-harness-hub
- personal-assistant
- personal_productivity
- text
- tool_use
library_name: open-harness-hub
pipeline_tag: text-generation
language:
- en
region:
- personal_productivity
- cross_industry
---

# Persistent chat with memory (multi-turn, preference-aware)

<!-- Generated from OpenHubForAI manifest `harness/chat-with-memory` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Multi-turn chat harness with persistent memory across sessions.
Loads user preferences, recalls prior conversation context, and
honors the user's stated rules (don't reveal X, always cite Y,
decline Z requests).

Memory layers (Anthropic Memory tool / OpenAI threads /
LangGraph checkpointer / local file) are abstracted via
`memory_backend` config.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `privacy` layer
- `tools` layer

**Industries**: personal_productivity, cross_industry
**Capabilities**: dialogue, memory, tool_use
**Modalities**: text
**Trust boundary**: local

## How the harness runs

### user turn → memory recall → preference check → response (tools as needed)

1. load user preferences
2. recall conversation history (last N turns + summary of older turns)
3. for each user turn:
4.   detect intent (Q&A / action-request / vent / coaching / silent)
5.   if action-request: check tool_autonomy preference
6.   generate response respecting preferences
7.   optionally call tools (calendar / search / email-draft)
8.   redact PII from any externally-bound output
9.   persist turn to memory backend

## Privacy boundaries

- **raw_input**: stays in the memory backend the user owns
- **derived_output**: stays with the user
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `anthropic_claude` | `anthropic` | external |
| `local_ollama` | `ollama` | local |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{chat-with-memory_open_harness_hub,
  title  = {Persistent chat with memory (multi-turn, preference-aware)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/chat-with-memory},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/chat-with-memory`.
