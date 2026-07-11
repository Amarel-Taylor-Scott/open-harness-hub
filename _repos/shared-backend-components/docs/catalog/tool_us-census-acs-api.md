# US Census ACS Data API

*tool* · `tool/us-census-acs-api` · v0.1.0 · experimental

Fetches authoritative American Community Survey estimates from the U.S.
Census Data API for a set of variables and a geography. Returns current,
citeable figures (population, income, housing, education, employment, …).

Capability lift: a bare LLM cannot reliably recall current ACS values for an
arbitrary place, and invents variable codes. This tool returns the real value
with its variable code and geography, so a pipeline can verify and cite it.
Pair with knowledge-pack/us-census-api-reference for the variable vocabulary.

| axis | value |
|---|---|
| industry | government, finance, cross_industry |
| capability | retrieval, tool_use, verification |
| modality | structured, tabular |
| lifecycle | experimental |
| trust_boundary | external |
| freshness | volatile |
| license | MIT |



