# LLM-as-judge success-criterion evaluator

*processor* · `processor/verify-llm-judge-criterion` · v0.1.0 · beta

Evaluates one `kind: llm_judge` success criterion. Wraps
`processor/llm-judge` but with an explicit pass/fail threshold
and a clear criterion label. The judge adapter is configurable
(default: deterministic baseline; override with
judge_adapter=adapter/anthropic-claude-sonnet for frontier
grading).

Returns the judge's score AND the pass-vs-threshold boolean.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | verification, evaluation |
| modality | text |
| lifecycle | beta |
| trust_boundary | mixed |
| license | MIT |



