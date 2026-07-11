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

## Registry replay audits and coverage repair (consolidated)

> Folds the durable design of the merged index plans — the partition registry replay audits and the index coverage repair planner. Frozen per-run counts live in the archived sources.

### Partition registry + replay audits

Additive ingestion only works if each small update can be proven correct without rebuilding the whole catalog. A partition registry is the compact control plane: it lists current partition manifests, their hashes, delta files, and object counts. Replay audits read the registry and apply each index delta into an in-memory index state (`partition manifests → registry → replay delta JSONL → replay report → publish affected keyword/vector/graph/facet updates`), failing when deltas are missing, duplicated, tampered with, or unsupported. Quality gates: registry freshness (every manifest path exists with the expected hash), partition uniqueness (unique `partition_id`), delta idempotency (unique `delta_id`, stable replay-policy key), content integrity (delta content hash matches the embedded `index_record`), operation support (only `upsert`/`replace`/`delete`), and repair locality (a bad shard repairs its affected partition, not a global rebuild). Runner: `scripts/factory/partition_registry_replay` (carries `--self-test`).

### Index coverage repair (fast feedback before promotion)

High-volume factories must not discover missing search records only at promotion-readiness time. The coverage repair planner (`scripts/db/index_coverage_repair_plan`) checks staged component rows for the expected hybrid-search record set — keyword, vector, graph, facet, quality — and writes repair JSONL only (it never updates Postgres, pgvector, a search service, or a graph store). If a batch loses index rows through ID truncation, duplicate collapse, partial generation, or worker failure, the planner produces explicit missing-index records before promotion readiness blocks the batch. Repair output is still staged data; the next gates are load preflight → approved candidate-table load → embedding execution → promotion readiness → review resolution before tenant-visible publication.

