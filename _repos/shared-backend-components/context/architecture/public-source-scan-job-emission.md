# Public Source Scan Job Emission

Public source blueprints become useful at scale when they can be expanded into
queue-ready jobs. The scan job emitter turns each blueprint into a deterministic
chain of object-factory jobs:

1. `source_discovery`
2. `source_snapshot`
3. `page_to_markdown`
4. `source_ingest`
5. `entity_linking`
6. `fuzzy_dedupe`
7. `dedupe_index`
8. `publish_review`

Each job has a stable ID, shard ID, parent dependency, tenant ID, policy block,
expected outputs, and audit metadata. Jobs store source patterns and extraction
contracts, not scraped source bodies.

## Why This Matters

At million-object scale, workers need more than a list of sources. They need
small, retryable units with clear costs, policies, and dependencies. This lets
Render workers, Cloud Run jobs, local queues, or tenant-hosted workers process
the same blueprint without changing the registry contract.

## Guardrails

Every emitted job carries:

- `redact_before_external_model: true`
- license posture from the source blueprint
- privacy boundary and trust tier
- excluded scopes
- no raw private data storage
- no source-body republication unless licensing allows it

The public catalog can publish the blueprint and job plan. Actual captures,
derived private objects, and tenant-owned source material remain behind the
deployment boundary that generated them.

## From blueprint to loaded rows (consolidated)

> Folds the durable design of the merged public-source plans — the job replay runner, the replay row emitter, and the load plan. Together they form the additive path from a published blueprint to committed Postgres/pgvector rows without network scraping. Frozen per-run sample counts live in the archived sources.

Additive path to a million objects: emit blueprints → expand into queue-ready jobs (above) → replay/execute by shard → write partition manifests per row family → bulk-load validated rows → replay index deltas without a full rebuild.

### Job replay runner (`scripts/factory` replay layer)

Scan jobs get a replay layer before they become production workers. The runner consumes queued `object-factory-job` JSONL, records what *would* run, emits deterministic output pointers, and writes `job-run-records.jsonl` (job id, input hash, expected row families, output pointers, policy summary, audit metadata), `checkpoint.json` (completed job ids + input hashes), and `partition-manifests.jsonl` compatible with the partition registry tooling. It is dry-run by default and never fetches source bodies. Resume semantics: each job is keyed by `job_id` + a hash of the full payload — an unchanged job is skipped; a changed payload re-emits and updates the checkpoint, so new shards, changed policies, or new blueprints rerun without deleting older partitions. Guardrails: run records point at object-storage paths instead of inlining bodies; policies preserve trust/privacy boundary, redaction requirement, excluded scopes, and budget; manifests state whether PII was detected, whether redaction occurred, and whether publication is allowed.

### Replay row emitter

Turns replay run records into the canonical JSONL row families (`source_record`, `normalized_object`, `canonical_entity`, `object_entity_ref`, `dedupe_cluster`, `label_assignment`, `dimension_value`, `object_embedding`, `index_record`, `review_ticket`). It is conservative — it consumes blueprint metadata + replay audit records, never fetches pages/PDFs/bodies, and keeps `insurance` in excluded scope. For each `source_ingest` replay record it creates candidate primitives from the blueprint's expected object types, each linked to a source record, blueprint source entity, vertical concept, and required workflow stages. This tests the whole source-surface-to-database path without scraping; real container workers later replace synthetic bodies with source-derived rows under the same row-family contracts.

### Load plan (JSONL → Postgres/pgvector staging)

The handoff from row-family JSONL to durable storage runs four gates: (1) relationship preflight — object/source/entity/dedupe/review/label/dimension/embedding ids all resolve before storage; (2) promotion scoring — hold/promote/review decisions, with volatile or high-risk public-source objects defaulting to review; (3) bulk-copy export — JSONL → CSV staging + `load.sql` for canonical tables and pgvector embeddings; (4) safety notes keeping the public catalog metadata-only until a governed worker has license, privacy, and quality clearance. A worker can process one partition and preserve promotion decisions without touching unrelated partitions; later reruns load only new/changed partitions while dedupe clusters, graph links, and index deltas stay stable.
