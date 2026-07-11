# Tool-validation success-criterion evaluator

*processor* · `processor/verify-tool-validate-criterion` · v0.1.0 · beta

Evaluates one `kind: tool_validate` success criterion. Invokes
an external tool (e.g. `tool/json-schema-validator`,
`tool/run-unit-tests`, `tool/iban-checker`) against the target.
Passes iff the tool returns success.

Use for: 'output validates against schemas/X.schema.json',
'generated code passes pytest', 'extracted IBAN passes mod-97',
'rendered HTML passes axe-core accessibility audit'.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | verification, evaluation, tool_use |
| modality | text, structured |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



