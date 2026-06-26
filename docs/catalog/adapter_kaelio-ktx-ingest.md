# Kaelio ktx ingest (warehouse → reviewable context files)

*adapter* · `adapter/kaelio-ktx-ingest` · v0.1.0 · experimental

Wraps `ktx ingest` (Apache-2.0, YC X25) as a pre-LLM normalization
Action: samples warehouse tables, ingests wiki/dbt/LookML/Metabase/Notion
sources, and emits reviewable semantic-layer YAML + Markdown wiki files in
git — exactly the artifact shape Baltor can then verify, sign, and put
under CDC. Their local .ktx/ingest-evidence dirs become INPUT to our
provenance rail. Sandbox policy forces KTX_TELEMETRY_DISABLED=1 and
DO_NOT_TRACK=1 (default-on PostHog telemetry upstream). LLM-heavy:
~19 min for a 20-table Postgres on upstream's own numbers; cost rides
our model keys.
WRAP CANDIDATE (discovery ≠ trust): admitted from the 2026-06 YC/tool
landscape research as a governed CANDIDATE behind a port — its output is
never served as truth, it is sandboxed, and measured lift is PENDING
(two-axis gate: lift AND structural durability) before any promotion.
Landscape record: archive/legacy/docs/strategy/yc-context-landscape-2026-06.md.

| axis | value |
|---|---|
| industry | ai, cross_industry, finance |
| capability | format_conversion, extraction, retrieval, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | external |
| license | MIT |



