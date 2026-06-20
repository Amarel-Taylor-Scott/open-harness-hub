# CDC event emitter

*tool* · `tool/cdc-event-emitter` · v0.1.0 · experimental

Emits change-data-capture events for component definition updates into the
component_change_event table defined in db/postgres/schema.sql.

For each component version transition (create, update, supersede, deprecate,
source refresh, hash recompute, publisher sign), computes canonical
definition hashes for the previous and new component_version rows, detects
changed fields, resolves actor metadata, and writes a deterministic
component_change_event row. Also emits corresponding index_record deltas and
optional review_ticket rows when changes cross high-risk thresholds (e.g.,
content hash mismatch, publisher signature missing, promotion_state
regression).

Designed to run after any factory batch, promotion decision, or curator edit.
Hash computation is content-driven so formatting-only changes do not produce
false new_definition_hash values.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, verification, retrieval, evaluation |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



