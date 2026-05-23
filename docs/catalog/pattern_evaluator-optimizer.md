# Evaluator-Optimizer

*pattern* · `pattern/evaluator-optimizer` · v0.1.0 · stable

One LLM call generates a candidate output; a second LLM (or processor)
evaluates against a rubric and provides specific feedback; the
generator revises. Loops until the evaluator passes. Distinguishes
itself from Self-Refine by using a SEPARATE evaluator (often a
stronger model) and a SPECIFIC rubric.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | reasoning, evaluation |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | CC-BY-4.0 |



