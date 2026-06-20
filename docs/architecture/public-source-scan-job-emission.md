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
