# Code-act Jupyter loop

*pipeline* · `pipeline/code-act-jupyter-loop` · v0.1.0 · beta

The OpenInterpreter pattern: model emits Python code in fenced
blocks, runtime renders the message + executes the code in a
Jupyter kernel, streams the observation back into the model's
context, loops until the model emits a `DONE` marker.

Verified by Open Harness Hub mining of the OpenInterpreter clone:
`interpreter/core/respond.py` implements exactly this loop.

| axis | value |
|---|---|
| industry | ai, software |
| capability | agent_loop, code_synthesis, tool_use |
| modality | text, code |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



## Task

Given a natural-language goal, generate Python code → execute in
Jupyter sandbox → observe output → iterate until the model
declares the task done or max_iterations is hit.

**pipeline_kind:** `code_act`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard_goal` | rule_pack | `rule-pack/grep-cloud-secrets` | — |
| 2 | `loop` | processor | `processor/iterative-revise-loop` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

