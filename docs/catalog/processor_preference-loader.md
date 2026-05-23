# User preference loader

*processor* · `processor/preference-loader` · v0.1.0 · stable

Load the user's preference file from
`knowledge-pack/user-preference-schema` (or per-user overrides),
resolve any inheritance from defaults, and emit a structured
preference object that downstream steps can consult.

Used at the start of any personal-assistant harness execution
to ensure preferences are HONORED, not assumed.

| axis | value |
|---|---|
| industry | personal_productivity, cross_industry |
| capability | memory, retrieval |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



