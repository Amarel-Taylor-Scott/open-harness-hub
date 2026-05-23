# Regex success-criterion evaluator

*processor* · `processor/verify-regex-criterion` · v0.1.0 · stable

Evaluates one `kind: regex` success criterion. Given a target
path (resolved from the pipeline trace) + a pattern + a
`must_match` flag, returns a pass/fail record with the matched
span (if any).

Use in `success_criteria:` lists alongside other criterion kinds
(semantic / llm_judge / deterministic / tool_validate / composite).

| axis | value |
|---|---|
| industry | cross_industry |
| capability | verification, evaluation |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



