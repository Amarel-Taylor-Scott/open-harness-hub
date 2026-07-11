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

## Entity refs and embedding buckets (consolidated)

> Folds the durable design of the merged use-case seed plans — the entity-reference rows and the embedding buckets. Together with the label/dimension rows above, one seed-derived candidate emits: one `normalized_object`, one exact-hash `dedupe_cluster`, many `label_assignment` and `dimension_value` rows, many `canonical_entity` + `object_entity_ref` rows, one `review_ticket` on high/critical/regulated risk, and keyword/vector/graph/facet/quality `index_record` rows.

### Entity reference rows (graph-addressable seeds)

Labels make filtering flexible, but a million-object registry also needs graph-addressable entities so workers can compare, block, cluster, and rerank by shared verticals, jurisdictions, workflow stages, expected inputs/outputs, and risk concepts. The exporter emits `canonical_entity` (stable graph nodes from domains, label paths, label ancestors, input/output types, pipeline stages, risk tiers) and `object_entity_ref` (edges with roles `domain`, `risk_tier`, `label_path`, `label_ancestor`, `accepts`, `emits`, `requires_stage`). This keeps the hierarchy flexible without promoting every domain word into a top-level taxonomy field — `capability` and `modality` remain broad routing axes; detail lives in labels, dimensions, and entity refs. Index records carry linked entity IDs and graph edges in metadata so search workers combine keyword/vector/facet/graph evidence without changing the source object shape. Entity refs give comparison workers cheap blocking keys (same `domain`, shared `label_ancestor`, shared `requires_stage`, compatible `accepts`/`emits`, shared `risk_tier`), reducing n-by-m comparisons while still allowing fuzzy matching inside each block. Synthetic seeds keep insurance as an excluded scope carried in bodies, labels, dimensions, and warnings — no insurance-specific primitives are minted.

### Embedding buckets (cheap approximate routing before real vectors)

Generated primitives need approximate similarity routing before expensive embedding work runs. Each candidate emits one `object_embedding` row with `embedding_model: stub:deterministic-text-v1` (storing canonical embedding text, text hash, bucket, linked entity IDs, and a flag that a real embedding is still required — the vector column left blank so bulk loaders create the row without an embedding service), one `dimension_value` named `embedding_bucket`, and vector/graph/facet index metadata pointing at the embedding row. Buckets are deterministic: `seed-bucket/{domain}/{risk_tier}/{stage_signature}/{output_signature}` — a low-cost blocking key (not a final similarity score) that lets workers group by likely deployment family, skip unrelated comparisons, resume at bucket/leaf level, and backfill real embeddings later without changing object IDs. The string key is portable across Postgres, BigQuery, ClickHouse, Redis queues, and object-storage batch jobs.
