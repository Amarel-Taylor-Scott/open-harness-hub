---
name: code-act-jupyter
description: 'Harness that wraps a model call with a Python execution loop. The model
  emits `<code>...</code>` blocks; the harness runs them in a sandboxed Jupyter kernel;
  stdout / stderr / repr feed back into the next turn. Loop terminates when the model
  emits a `<final>... </final>` block or `max_tool_turns` is reached. The classic
  AIMO-2 + ChartQA + math-reasoning shape, verified by Open Harness Hub mining: itahiro
  DeepSeek-R1-distill-7B (1399 votes), lewtun "Updated Code Interpretation" (1173),
  abdurrafae (1001), mbmmurad QwQ-32B (1097).'
when_to_use: Use when the user needs reasoning. Use when the user needs tool_use.
  Use when the user needs code_execution. Particularly relevant for ai. Particularly
  relevant for scientific_research. Particularly relevant for education.
---

# Code-Act Jupyter (tool-augmented reasoning via sandboxed Python)

Harness that wraps a model call with a Python execution loop. The
model emits `<code>...</code>` blocks; the harness runs them in a
sandboxed Jupyter kernel; stdout / stderr / repr feed back into the
next turn. Loop terminates when the model emits a `<final>...
</final>` block or `max_tool_turns` is reached.

The classic AIMO-2 + ChartQA + math-reasoning shape, verified by
Open Harness Hub mining: itahiro DeepSeek-R1-distill-7B (1399
votes), lewtun "Updated Code Interpretation" (1173), abdurrafae
(1001), mbmmurad QwQ-32B (1097).

## Applied layers

- `persona`
- `tools`

## Prompt → code → execute → observe → repeat

*model_call:* `required`

**Steps**

1. compose persona + task
2. call model
3. extract <code>...</code> blocks
4. execute in sandbox kernel
5. feed observation back as user turn
6. stop on <final>...</final> or max_turns

**Verification**

- no shell escape / subprocess.run with untrusted args
- kernel restart on memory > 4GB or wall > 60s
- stdout truncated at 16KB per turn

## Privacy boundaries

- **raw_input**: stays local to the kernel process
- **derived_output**: transcript may be synced post-anonymization
- **external_calls**: kernel network egress is off by default

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_vllm` | `vllm` | local | False | True |
| `local_ollama` | `ollama` | local | False | False |

## Provenance

- Hub artifact: `harness/code-act-jupyter` v0.1.0
- License: `MIT`
- Lifecycle: `beta`
- Full source manifest: see `references/manifest.yaml`
