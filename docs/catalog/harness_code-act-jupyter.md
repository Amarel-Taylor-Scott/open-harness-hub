# Code-Act Jupyter (tool-augmented reasoning via sandboxed Python)

*harness* · `harness/code-act-jupyter` · v0.1.0 · beta

Harness that wraps a model call with a Python execution loop. The
model emits `<code>...</code>` blocks; the harness runs them in a
sandboxed Jupyter kernel; stdout / stderr / repr feed back into the
next turn. Loop terminates when the model emits a `<final>...
</final>` block or `max_tool_turns` is reached.

The classic AIMO-2 + ChartQA + math-reasoning shape, verified by
Open Harness Hub mining: itahiro DeepSeek-R1-distill-7B (1399
votes), lewtun "Updated Code Interpretation" (1173), abdurrafae
(1001), mbmmurad QwQ-32B (1097).

| axis | value |
|---|---|
| industry | ai, scientific_research, education |
| capability | reasoning, tool_use, code_execution |
| modality | text, code |
| lifecycle | beta |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Consumes:** `tool_definition`, `persona_block`

**Emits:** `reasoning_step`, `tool_call`, `tool_observation`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_vllm` | `vllm` | local | False | True |
| `local_ollama` | `ollama` | local | False | False |

## Logic paths

### Prompt → code → execute → observe → repeat  
*model_call: `required`*

1. compose persona + task
1. call model
1. extract <code>...</code> blocks
1. execute in sandbox kernel
1. feed observation back as user turn
1. stop on <final>...</final> or max_turns

**consumes:** `tool_definition`, `persona_block`

**emits:** `tool_call`, `tool_observation`, `reasoning_step`

**verification:** no shell escape / subprocess.run with untrusted args, kernel restart on memory > 4GB or wall > 60s, stdout truncated at 16KB per turn



## Privacy boundaries

- **raw_input**: stays local to the kernel process
- **derived_output**: transcript may be synced post-anonymization
- **external_calls**: kernel network egress is off by default

