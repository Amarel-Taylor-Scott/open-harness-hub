# Reasoning framework selector

*processor* · `processor/reasoning-framework-selector` · v0.1.0 · experimental

Pick a reasoning framework (CoT / ReAct / Tree-of-Thoughts /
Skeleton-of-Thought / Program-of-Thought / Self-Consistency / none)
based on the task profile. Cheap heuristic up front; can also call a
small classifier model.

Selector heuristics:
  - CoT for multi-step math / logic, deterministic answer expected
  - Self-Consistency on top of CoT for arithmetic / olympiad-level
  - ReAct for tool-use loops
  - Tree-of-Thoughts for exploratory planning with branching
  - SoT for parallelizable structured outputs (lists, tables, code skeletons)
  - PoT for problems best expressed as Python
  - none for simple lookup / classification

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | routing, classification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



