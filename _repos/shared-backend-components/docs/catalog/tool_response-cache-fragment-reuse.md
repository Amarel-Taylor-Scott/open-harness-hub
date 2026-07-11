# Response cache fragment reuse

*tool* · `tool/response-cache-fragment-reuse` · v0.1.0 · experimental

Caches prior model response fragments keyed by a content hash of
the canonical request (prompt text + parameters digest). On a
cache hit, returns the stored fragment immediately without
contacting the model, recording latency and cost savings. On a
miss, the caller dispatches to the model, then stores the fragment
via the write endpoint. Supports TTL-based expiry, namespace
isolation for tenant deployments, and partial fragment stitching
when only portions of a composite request are cached.

| axis | value |
|---|---|
| industry | ai, cross_industry, software.devops |
| capability | serving, retrieval, format_conversion |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



