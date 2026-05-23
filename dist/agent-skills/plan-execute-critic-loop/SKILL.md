---
name: plan-execute-critic-loop
description: 'Given a goal, repeatedly: PLAN (LLM proposes steps) → EXECUTE (run tools
  for each step) → CRITIQUE (LLM checks output against goal + flags failures) → either
  DONE or REPLAN. Caps at max_iterations and emits a full trace.'
when_to_use: 'Pipeline kind: plan_and_execute.'
---

# Plan / execute / critic loop

The classic agentic pattern: planner LLM drafts a step list, executor
runs the steps (with tool calls), critic LLM reviews the trace + re-plans
on failure. Iterates until either the goal is achieved or a max-iteration
cap is hit. Mirrors langchain-ai/langgraph `examples/plan-and-execute`,
Anthropic cookbook `patterns/agents/evaluator-optimizer`, and OpenAI
swarm handoff routing.

## Task

Given a goal, repeatedly: PLAN (LLM proposes steps) → EXECUTE (run tools
for each step) → CRITIQUE (LLM checks output against goal + flags failures)
→ either DONE or REPLAN. Caps at max_iterations and emits a full trace.

## Steps

1. **redact_goal** — `harness` → `harness/redact-pii-text`
2. **guard_input** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
3. **plan** — `harness` → `harness/text-safety-review`
4. **execute_loop** — `loop` → `processor/cost-ceiling-gate` (when `$.inputs.max_iterations > 0`)
5. **critique** — `processor` → `processor/self-refine-critique`
6. **trace_emit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`, `rule-pack/privacy-pii-text-en`

## Success criteria

- rubric `rubric/research-entity-v1` threshold 0.65

## Provenance

- Hub artifact: `pipeline/plan-execute-critic-loop` v0.1.0
- License: `MIT`
- Industry: cross_industry
- Full source manifest: see `references/manifest.yaml`
