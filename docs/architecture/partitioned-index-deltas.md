# Partitioned Index Deltas

At one million or ten million primitives, the registry cannot treat every source-derived object as a standalone catalog page. High-volume objects should live in JSONL shards, and each shard should emit append-only index deltas for keyword, vector, graph, facet, quality, freshness, cost, and review queues.

The static catalog remains the curated public surface. The operational database and search system consume partition manifests and index deltas.

## Flow

```text
source records
-> normalized object JSONL shard
-> partition manifest
-> index delta JSONL
-> keyword/vector/graph/facet upserts
-> review queues
```

## Partition Manifest

A partition manifest records the batch boundary:

- `partition_id`: stable shard id such as `normalized-objects/research-web/2026-05-25/000001`.
- `partition_kind`: normalized objects, labels, dimensions, index records, review tickets, embeddings, or graph edges.
- `run_id`: object-factory run that produced it.
- `object_count`: number of records in the shard.
- `shard_paths`: raw or normalized JSONL inputs.
- `index_delta_paths`: derived delta JSONL outputs.
- `content_hash`: hash over source shard content and schema version.
- `privacy_summary`: whether the partition is redacted and publishable.
- `quality_summary`: counts for accepted, review-needed, rejected, duplicate, or tombstoned records.

## Index Delta Record

An index delta is an idempotent operation:

```json
{
  "delta_id": "delta:partition:00000001:keyword",
  "partition_id": "partition:demo",
  "operation": "upsert",
  "index_record": {
    "index_record_id": "idx:object:keyword",
    "index_kind": "keyword",
    "subject_id": "object:demo",
    "subject_type": "normalized_object",
    "text": "searchable text",
    "metadata": {}
  }
}
```

The same delta can be replayed. Consumers should use `delta_id` or `replay_policy.idempotency_key` to make writes idempotent.

## Why This Matters

Full rebuilds become impossible at scale:

- 1M objects as Markdown pages would make docs slow and mostly unusable.
- 10M objects require append-only shards, replayable queues, and partition-level repair.
- Vector and graph stores need batched upserts, not static-site generation.
- Review workflows need quarantine at partition level, not global rebuild locks.

The working rule is: curated manifests get pages; high-volume objects get partitions, deltas, indexes, and sampled summaries.

