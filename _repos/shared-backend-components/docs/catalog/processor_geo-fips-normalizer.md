# Geographic identifier → FIPS normalizer

*processor* · `processor/geo-fips-normalizer` · v0.1.0 · experimental

Deterministic standardization of free-text US geography references (state
names/abbreviations, county names, place names, ZIP/ZCTA) into canonical FIPS
codes and the Census `for`/`in` clauses that `tool/us-census-acs-api` needs.

Capability lift: a bare LLM guesses FIPS codes and mangles the for/in clause
syntax. This processor resolves them deterministically (no model call), so the
downstream API call is correct and replayable.

| axis | value |
|---|---|
| industry | government, cross_industry |
| capability | format_conversion, extraction |
| modality | structured, spatial |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



