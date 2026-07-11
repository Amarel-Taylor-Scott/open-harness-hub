# Component CDC Versioning

Component rows need the same change discipline as public facts. At million-object scale, a component is not just a static definition: it may be refreshed from a public source, signed by a publisher, superseded by a curator, or updated by a worker after dedupe and review.

## Database Shape

The canonical path is:

- `component`: active reusable component row.
- `component_version`: immutable version body plus canonical `definition_hash`.
- `source_record`: source URL, publisher, archive URL, trust tier, and `content_hash`.
- `component_change_event`: immutable CDC row linking previous and new hashes.
- `index_record`: freshness, keyword, graph, quality, and vector search projections.
- `review_ticket`: review route for source refreshes, signed publisher updates, and risky changes.

Repository component definitions remain useful as seed/export files, but hosted lifecycle state should be driven by Postgres rows.

## Hash Policy

Use separate hashes for separate jobs:

- `definition_hash`: sha256 over canonical JSON for the component version body.
- `content_hash`: sha256 over the source content or normalized object content.
- `change_event_id`: deterministic ID derived from component id, version id, and new definition hash.

Canonical JSON should sort keys and use stable compact separators. Raw file text should not be used for identity because whitespace and export order can create false changes.

## Review Routing

Automatic CDC is not automatic approval. Route to review when a change:

- touches volatile public facts;
- has a publisher signature or revocation reference;
- changes safety, legal, public health, financial, child-safety, or deployment behavior;
- changes tool permissions, external calls, model routing, or privacy boundaries;
- has unclear source licensing or provenance.

Low-risk metadata-only hash recomputes can flow to freshness indexes without promotion.

## Factory Use

The `component-cdc-planner` compares previous and new component version rows and emits:

- `component-change-events.jsonl`;
- `component-change-index-records.jsonl`;
- `component-change-review-tickets.jsonl`;
- CSV files for Postgres loading;
- `load-component-change-events.sql`.

This lets workers update signed facts, public health packs, procedure packs, and generated component candidates incrementally instead of rebuilding everything.
