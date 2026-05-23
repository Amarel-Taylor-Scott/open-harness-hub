# Deterministic comparison success-criterion evaluator

*processor* · `processor/verify-deterministic-criterion` · v0.1.0 · stable

Evaluates one `kind: deterministic` success criterion. Resolves a
target value from the pipeline trace and applies a comparison
operator (>, >=, <, <=, ==, !=, in, not_in, is_truthy, is_falsy)
against an expected value.

Use for: 'pipeline output count > 5', 'severity_counts.critical == 0',
'rule-pack fire count < 3', etc.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | verification, evaluation |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



