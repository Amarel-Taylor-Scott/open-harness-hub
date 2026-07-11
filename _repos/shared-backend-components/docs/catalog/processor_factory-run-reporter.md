# Factory run provenance + cost + quality reporter

*processor* · `processor/factory-run-reporter` · v0.1.0 · experimental

Writes a complete factory-run report to
`dist/factory-runs/{run_id}/` capturing:

 - run.json — top-level summary (walker, params, totals, costs)
 - walks/*.json — raw walker outputs
 - drafts/*.json — emitted drafts (mirrored copies)
 - rejected.json — quality-gate rejections with reasons
 - dedup.json — semantic-dedup hits with best matches
 - validation_failures.json — schema-validation failures
 - REPORT.md — human-readable summary

Every draft in `catalog/_inbox/` can be traced back to its
walker run + source node, enabling reproducibility and
accountability at 2000x scale.

| axis | value |
|---|---|
| industry | software, ai, cross_industry |
| capability | verification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



