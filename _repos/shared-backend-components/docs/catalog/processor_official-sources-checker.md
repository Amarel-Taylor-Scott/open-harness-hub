# Official-sources analyzer

*processor* · `processor/official-sources-checker` · v0.1.0 · experimental

Verify retrieved candidates against an allowlist of authoritative
sources (gov, intergovernmental, academic, standards bodies).
Returns per-candidate flags:
  - is_official: bool
  - authority_tier: enum [primary, secondary, tertiary, blog, unknown]
  - jurisdiction_match: did the source's jurisdiction match the
    query's geographic scope?
  - freshness_ok: source date within the requested window?
  - cross_referenced: does another official source corroborate?
Pairs naturally with `rule-pack/web-search-allowlist-default` and
the DueCare `official_sources` layer pattern.

| axis | value |
|---|---|
| industry | cross_industry, media, government, healthcare, finance |
| capability | verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | external |
| license | MIT |



