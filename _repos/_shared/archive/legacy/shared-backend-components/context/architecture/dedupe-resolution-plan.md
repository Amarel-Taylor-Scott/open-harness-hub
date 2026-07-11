# Dedupe Resolution Plan

Generated candidates should not be blocked forever by dedupe review, but dedupe clearance is not the same as content approval. The dedupe resolution planner separates those two decisions.

The planner reads:

- `dedupe-clusters.jsonl`
- `normalized-objects.jsonl`
- `component-candidates.jsonl`

It writes:

- `dedupe-resolutions.jsonl`
- `dedupe-resolutions.csv`
- `dedupe-index-records.csv`
- `dedupe-review-tickets.csv`
- `candidate-dedupe-review-updates.csv`
- `load-dedupe-resolutions.sql`
- `dedupe-resolution-plan.json`

## Resolution Actions

The first implementation uses conservative actions:

- `mark_singleton_resolved`: one public member, public privacy boundary, no duplicate conflict found.
- `merge_exact_duplicates`: multiple members with the same content hash or exact high-confidence match.
- `route_to_curator`: ambiguous clusters, non-public rows, or weak evidence.
- `hold_for_more_evidence`: insufficient evidence to decide.
- `reject_cluster`: invalid or unsafe cluster.

`mark_singleton_resolved` still leaves content approval outstanding. This is deliberate: resolving duplicate risk should not publish generated content as an active component.

## Database Role

The planner adds a `dedupe_resolution` table to the Postgres schema and emits load SQL for:

- `dedupe_resolution`
- `index_record`
- `review_ticket`
- `normalized_object.review_status`
- `component_candidate.review_status`

That gives review queues a durable state transition before the active component promotion planner runs.

## Current Seed Behavior

The current seed set has single-member public clusters for the generated public-source candidates. The planner marks those clusters as dedupe-resolved while routing the content to review. This clears the dedupe gate without weakening the publication gate.
