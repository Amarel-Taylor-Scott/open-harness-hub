# US Census Geocoder API

*tool* · `tool/us-census-geocoder-api` · v0.1.0 · experimental

Resolves a street address (or coordinates) to a standardized address plus its
Census geographies: state/county FIPS, tract, block, and GEOID. The bridge
from messy address strings to the geography codes the ACS API needs.

Capability lift: a bare LLM cannot reliably map an address to its census tract
or county FIPS. This tool returns the canonical geographies deterministically,
enabling address → FIPS → ACS-figure grounding chains.

| axis | value |
|---|---|
| industry | government, cross_industry |
| capability | retrieval, tool_use, format_conversion |
| modality | structured, spatial |
| lifecycle | experimental |
| trust_boundary | external |
| freshness | stable |
| license | MIT |



