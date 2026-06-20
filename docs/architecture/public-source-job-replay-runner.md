# Public Source Job Replay Runner

Public-source scan jobs need a replay layer before they become production
workers. The replay runner consumes queued object-factory jobs, records what
would run, emits deterministic output pointers, and writes partition manifests
plus a checkpoint.

This gives the platform an additive path to one million objects:

1. emit public-source blueprints;
2. expand them into queue-ready jobs;
3. replay or execute jobs by shard;
4. write partition manifests for each row family;
5. bulk-load validated rows into Postgres/pgvector;
6. replay index deltas without rebuilding the whole catalog.

## Contract

The runner reads `object-factory-job` JSONL and emits:

- `job-run-records.jsonl` with job id, input hash, expected row families,
  output pointers, policy summary, and audit metadata;
- `checkpoint.json` with completed job ids and input hashes;
- `partition-manifests.jsonl` plus per-partition `partition-manifest.json`
  files compatible with the partition registry tooling.

The initial implementation is dry-run by default. It does not fetch source
bodies or republish scraped material. Later container workers can replace the
dry-run output pointers with real JSONL row families while preserving the same
checkpoint and partition contracts.

## Resume Semantics

Each job is keyed by `job_id` and a hash of the full job payload. If the same
job id and hash already appear in the checkpoint, the runner skips it. If the
payload changes, the job is emitted again and the checkpoint is updated.

This is the additive behavior needed for 1M to 10M objects: workers can rerun
new shards, changed policies, or new blueprints without deleting older
partitions.

## Guardrails

- Run records point to object-storage paths instead of inlining source bodies.
- Policies preserve trust boundary, privacy boundary, redaction requirement,
  excluded scopes, and budget.
- Partition manifests explicitly state whether PII was detected, whether
  redaction occurred, and whether publication is allowed.
- Source bodies remain behind the deployment boundary until a later governed
  worker has license and privacy clearance to extract publishable objects.
