# Sanctions list (shape, with placeholder entries)

*knowledge-pack* · `knowledge-pack/sanctions-list-shape` · v0.1.0 · experimental

Reference SHAPE for sanctions list integration. Real data must be
pulled from OFAC, UN, EU, HMT, or the institution's licensed
provider; this pack illustrates the row schema, not the entries.
Each row is an entity (individual or organization) with
normalized name, source list, listing date, and aliases.

| axis | value |
|---|---|
| industry | finance, finance.aml, finance.kyc |
| capability | retrieval, verification |
| modality | structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | CC0-1.0 |



