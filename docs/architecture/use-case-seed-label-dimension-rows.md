# Use Case Seed Label and Dimension Rows

Use-case seeds are useful only if they become searchable, filterable factory
records. This batch converts broad seed surfaces into candidate primitives plus
loadable `label_assignment` and `dimension_value` rows.

## Row Families

The exporter emits:

- `source_record` for the seed batch;
- `normalized_object` rows with `object_type: candidate_primitive`;
- `dedupe_cluster` rows based on deterministic content hashes;
- `label_assignment` rows for domain, risk, output type, excluded scope, and
  flexible hierarchy paths such as `vertical.trades.*`;
- `dimension_value` rows for risk score, stage count, input count, output
  count, human-review need, and excluded scopes;
- `review_ticket` rows for high-risk seeds;
- `index_record` rows for keyword, vector, graph, facet, and quality indexes.

## Scope Boundary

Insurance-related use-case seeds are excluded by default. The row exporter
keeps the exclusion explicit as both labels and dimensions so downstream search,
promotion, and deployment routing can filter them out.

## Why This Matters

Core `capability` and `modality` values should stay small and stable. New
verticals such as trades, oil and gas, animal hospitals, banking laws, creative
workflows, and geographic law analysis should be represented through flexible
labels and dimensions. This avoids vocabulary churn while still making the
registry specific enough for practical search and automated pipeline assembly.
