# Date parse multi-format → ISO 8601

*processor* · `processor/date-parse-multiformat` · v0.1.0 · stable

Parse any date string in 50+ common formats (MM/DD/YYYY, DD/MM/YYYY,
YYYY-MM-DD, Mar 5 2025, 5-Mar-25, 1709589600 epoch, ISO 8601
fragments, RFC 2822) into a normalized ISO 8601 datetime. Resolves
ambiguous M/D order using locale hint. Preserves timezone if
given, defaults to UTC otherwise.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | format_conversion, extraction |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



