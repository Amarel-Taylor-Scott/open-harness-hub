# US Census API reference (ACS variables + geography hierarchy)

*knowledge-pack* · `knowledge-pack/us-census-api-reference` · v0.1.0 · experimental

Grounding facts a bare LLM does not hold reliably: the exact American
Community Survey (ACS) variable codes (e.g. B19013_001E = median household
income, B01003_001E = total population) and the Census geography hierarchy +
`for`/`in` clause syntax used by the Census Data API.

Capability lift: models hallucinate variable codes and current figures.
Pairing this reference with `tool/us-census-acs-api` lets a pipeline fetch the
authoritative, current value and cite it, instead of guessing.

Geography hierarchy (coarse → fine): us → region → division → state → county →
county subdivision → tract → block group → block; plus place, ZCTA,
congressional district, and metropolitan/micropolitan statistical area (CBSA).

| axis | value |
|---|---|
| industry | government, cross_industry |
| capability | retrieval, verification |
| modality | structured, tabular |
| lifecycle | experimental |
| trust_boundary | external |
| freshness | stable |
| license | CC-BY-4.0 |



