# Composite (AND/OR/NOT) success-criterion evaluator

*processor* · `processor/verify-composite-criterion` · v0.1.0 · stable

Evaluates one `kind: composite` success criterion. Combines child
criteria with AND / OR / NOT semantics. Children may themselves be
composite — arbitrarily deep nesting allowed. Short-circuits where
possible (AND stops at first failure; OR stops at first pass).

Use to express: '(critical-red-flags-found AND remediation-proposed)
OR clean-baseline', 'PHI-redacted AND (rubric-score >= 0.7 OR
human-reviewed)', etc.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | verification, evaluation |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



