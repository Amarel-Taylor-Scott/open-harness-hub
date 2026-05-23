# Plan / execute / critic loop

*pipeline* · `pipeline/plan-execute-critic-loop` · v0.1.0 · experimental

The classic agentic pattern: planner LLM drafts a step list, executor
runs the steps (with tool calls), critic LLM reviews the trace + re-plans
on failure. Iterates until either the goal is achieved or a max-iteration
cap is hit. Mirrors langchain-ai/langgraph `examples/plan-and-execute`,
Anthropic cookbook `patterns/agents/evaluator-optimizer`, and OpenAI
swarm handoff routing.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | planning, agent_loop, reasoning |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given a goal, repeatedly: PLAN (LLM proposes steps) → EXECUTE (run tools
for each step) → CRITIQUE (LLM checks output against goal + flags failures)
→ either DONE or REPLAN. Caps at max_iterations and emits a full trace.

**pipeline_kind:** `plan_and_execute`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `redact_goal` | harness | `harness/redact-pii-text` | — |
| 2 | `guard_input` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 3 | `plan` | harness | `harness/text-safety-review` | — |
| 4 | `execute_loop` | loop | `processor/cost-ceiling-gate` | $.inputs.max_iterations > 0 |
| 5 | `critique` | processor | `processor/self-refine-critique` | — |
| 6 | `trace_emit` | processor | `processor/audit-trace-emitter` | — |

