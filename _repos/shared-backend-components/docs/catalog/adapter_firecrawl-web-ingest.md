# Firecrawl web ingestion (site → clean markdown)

*adapter* · `adapter/firecrawl-web-ingest` · v0.1.0 · experimental

Wraps Firecrawl (YC S22, $16.2M) as an ingestion-provider
candidate: crawl/scrape → clean markdown + structured data for pipeline
intake. Output lands as source_record rows with capture timestamps and
source handles; never as facts. Pairs with the source-governance and
dedupe stages.
WRAP CANDIDATE (discovery ≠ trust): admitted from the 2026-06 YC/tool
landscape research as a governed CANDIDATE behind a port — its output is
never served as truth, it is sandboxed, and measured lift is PENDING
(two-axis gate: lift AND structural durability) before any promotion.
Landscape record: docs/strategy/yc-context-landscape-2026-06.md.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | extraction, retrieval |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | external |
| license | MIT |



