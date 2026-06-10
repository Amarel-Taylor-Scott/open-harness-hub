# Public Source Load Plan

Public-source replay rows are useful only when they can move into durable
storage without losing provenance, review gates, or resume state. The load-plan
layer is the handoff from JSONL row families to Postgres and pgvector staging.

## Inputs

The load-plan emitter consumes a row directory with the canonical factory row
families:

- source records;
- normalized objects;
- canonical entities and object/entity refs;
- dedupe clusters;
- labels and dimensions;
- embedding work items;
- index records;
- review tickets.

These rows are generated from public-source blueprint and replay metadata. Raw
source captures, private documents, emails, proprietary source dumps, and other
source bodies remain outside the public catalog.

## Gates

The load plan runs four gates:

1. Relationship preflight checks that object ids, source ids, entity ids,
   dedupe members, review tickets, labels, dimensions, and embedding work items
   resolve before storage.
2. Promotion scoring emits hold/promote/review decisions from normalized
   objects. For this path, volatile or high-risk public-source objects should
   default to review before broad publication.
3. Bulk-copy export converts JSONL into CSV staging files plus `load.sql` for
   canonical Postgres tables and pgvector-compatible embeddings.
4. Safety notes keep the public catalog metadata-only until a governed worker
   has license, privacy, and source-quality clearance.

## Scaling Role

This is the layer that lets the registry grow additively. A worker can process
one partition, emit row families, generate a load plan, and preserve promotion
decisions without touching unrelated partitions. Later reruns can load only new
or changed partitions while keeping dedupe clusters, graph links, and index
deltas stable.
