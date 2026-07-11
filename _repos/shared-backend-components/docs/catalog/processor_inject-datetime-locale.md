# Inject datetime + locale into prompt

*processor* · `processor/inject-datetime-locale` · v0.1.0 · stable

Replace placeholders like `{{now}}`, `{{today}}`, `{{user_timezone}}`,
`{{user_locale}}`, `{{user_currency}}` in the prompt template with the
actual values at request time. Fixes the "stale knowledge cutoff" issue
where the model otherwise has no idea what today's date is.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | format_conversion |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



