# Partition Registry Replay Audits

Additive ingestion only works if each small update can be proven correct without rebuilding the entire catalog. A partition registry is the compact control plane for that proof: it lists the current partition manifests, their hashes, their delta files, and their object counts.

Replay audits read the registry and apply each index delta into an in-memory index state. The audit fails when deltas are missing, duplicated, tampered with, or unsupported.

## Workflow

```text
partition manifest files
-> partition registry
-> replay index delta JSONL
-> replay report
-> publish affected keyword/vector/graph/facet updates
```

## Quality Gates

- Registry freshness: every manifest path exists and has the expected hash.
- Partition uniqueness: every `partition_id` is unique in the registry.
- Delta idempotency: every `delta_id` is unique and every replay policy has a stable key.
- Content integrity: every delta content hash matches the embedded `index_record`.
- Operation support: replay accepts only supported operations such as `upsert`, `replace`, and `delete`.
- Repair locality: a bad shard should trigger repair of the affected partition, not a global rebuild.

## Local Commands

```bash
python3 -m scripts.factory.partition_registry_replay --self-test
python3 -m scripts.factory.partition_registry_replay \
  --manifest-dir dist/index-deltas/demo \
  --registry-output dist/partition-registry.json \
  --replay-report-output dist/replay-report.json
```

This pattern keeps the public static site curated and small while operational search systems consume high-volume partitions and replayable deltas.
