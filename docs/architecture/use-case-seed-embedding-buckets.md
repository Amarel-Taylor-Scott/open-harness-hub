# Use Case Seed Embedding Buckets

Generated primitives need approximate similarity routing before expensive
embedding work runs. The seed row exporter emits deterministic embedding stubs
and bucket dimensions so comparison jobs can reduce candidate pairs cheaply,
then later replace the stub with a real pgvector embedding.

## Output Rows

Each candidate primitive emits:

- one `object_embedding` row with `embedding_model:
  stub:deterministic-text-v1`;
- one `dimension_value` named `embedding_bucket`;
- vector `index_record` metadata that points at the embedding row;
- graph and facet index metadata that carries the same bucket and entity IDs.

The stub row stores the canonical embedding text, text hash, bucket, linked
entity IDs, and a flag that a real embedding is still required. The vector
column is intentionally blank so bulk loaders can create the row without
requiring an embedding service.

## Bucket Shape

Buckets are deterministic:

`seed-bucket/{domain}/{risk_tier}/{stage_signature}/{output_signature}`

This gives workers a low-cost blocking key based on the broad domain, review
risk, required pipeline stages, and output compatibility. It is not a final
similarity score. It is an early pruning layer before lexical comparison,
entity overlap, and real dense-vector search.

## Why This Matters

At 1M to 10M objects, all-pairs comparison is not viable. A cheap bucket lets
workers:

1. group candidate primitives by likely deployment family;
2. skip obviously unrelated comparisons;
3. resume comparison jobs at the bucket or leaf level;
4. backfill actual embeddings later without changing object IDs;
5. compare model/provider costs for embedding generation separately from
   source normalization.

The bucket is also portable: Postgres, BigQuery, ClickHouse, Redis queues, and
object-storage batch jobs can all use the same string key.
