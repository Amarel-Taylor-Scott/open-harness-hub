# Tabular schema canonicalizer (column mapping + value standardization)

*processor* · `processor/tabular-schema-canonicalizer` · v0.1.0 · experimental

Maps an arbitrary input table to a declared canonical schema: fuzzy-matches
source column names to target fields, infers types, and standardizes values
(dates → ISO 8601, units → SI, currency → ISO 4217 minor units, booleans,
whitespace/case). Emits the column mapping, the standardized table, and any
unmapped columns for review.

Capability lift: this is the "messy spreadsheet → clean schema" step that a
bare LLM does inconsistently and unauditably across rows. Doing it
deterministically (with a confidence + an explicit unmapped list) makes the
result reproducible, cheap, and reviewable — and runs before any model call.

| axis | value |
|---|---|
| industry | cross_industry, finance, government |
| capability | format_conversion, extraction |
| modality | tabular, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



