# Plan-and-Execute

*pattern* · `pattern/plan-and-execute` · v0.1.0 · stable

Separate planning from execution. A planner LLM produces an explicit
step list; an executor (often a different / cheaper model) runs each
step. After execution, a re-planner can update the plan based on
results. Distinct from ReAct because ReAct interleaves reasoning
with each action; here planning happens up-front.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | planning, agent_loop |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | CC-BY-4.0 |



