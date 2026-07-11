# Source Surface Scan Partitions

The million-object factory needs a scheduler boundary between broad source
ideas and worker jobs. A source surface such as "public health safety facts" or
"workflow ecosystem templates" is too large to hand to a scraper directly. It
should first become deterministic partitions with resume cursors, review
policy, cost limits, and expected object contracts.

## Partition Contract

Each partition contains only metadata that is safe to publish:

- source surface id, vertical, title, publisher classes, and access methods;
- source patterns and expected object types;
- required stages: source governance, discovery, snapshot, page conversion,
  normalized extraction, entity linking, fuzzy dedupe, index emission, and
  review routing;
- deterministic cursor bucket and content hash;
- max-record budget and priority score;
- privacy, license, trust-tier, and excluded-scope policy.

Raw captures, private documents, screenshots, emails, and source bodies stay in
tenant storage or object storage. The public catalog stores only pointers,
hashes, manifests, summaries, and curated objects whose license permits reuse.

## Additive Growth

The partition planner writes three files:

- `source-surface-scan-partitions.jsonl` for the scheduler;
- `public-source-blueprints.jsonl` for the existing public-source scan job
  emitter;
- `source-surface-schedule-summary.jsonl` for curator review and progress
  reporting.

Because partition ids are deterministic, the same backlog can be rerun without
rebuilding all objects. Workers can record `resume_after`, object hashes,
promotion decisions, dedupe clusters, and index deltas per partition. This lets
the registry grow from thousands of objects to hundreds of thousands without
losing provenance or rerunning completed source windows.

## Priority

Backlog rows should use the same priority formula as the goal document:

`usefulness x demand x complexity x time_savings x frequency_of_deployment x not_solved_by_out_of_box_llms x cost_savings x deployment_management_value x model_swap_value`

High-priority partitions are not necessarily published first. High-risk
partitions, such as public health facts, legal requirements, AML alert review,
community moderation, or environmental safety thresholds, should emit review
tickets before promotion. Lower-risk workflow templates or model-card context
can flow through automated checks with sampled review.

## Worker Handoff

After partitioning, `public-source-blueprints.jsonl` can be passed into the
public-source scan job emitter. That second step expands each partition into
worker jobs for discovery, snapshot, conversion, ingest, entity linking,
dedupe, indexing, and review. Containerized workers can then scale horizontally
on Render, Cloud Run, or a queue-backed worker pool while keeping one narrow
contract per stage.

## Seed row emission and execution summary (consolidated)

> Folds the durable design of the merged source-surface plans — the seed row emitter and the execution summary. Frozen per-run manifest/object counts live in the archived sources.

### Seed row emitter

Converts each source surface into one candidate seed per declared primitive, then delegates to the canonical use-case seed row exporter, producing the standard factory row families (`source_record`, `normalized_object`, `canonical_entity`, `object_entity_ref`, `dedupe_cluster`, `label_assignment`, `dimension_value`, `object_embedding`, `review_ticket`, `index_record`). Each source surface carries a vertical, source surfaces, capability-gap reason, candidate primitives, labels, risk tier, and excluded scopes; every candidate primitive becomes a candidate object with source surfaces as expected inputs, the primitive name as expected output, and source-governance / entity-linking / fuzzy-dedupe / index-emission / review-routing as required stages. This keeps esoteric industries (automotive sales, employment agencies, plumbing/HVAC, woodworking, offshore oil and gas, environmental reviews) on the same storage and search path as broader seeds. High-risk source surfaces emit review tickets before promotion; synthetic seed metadata can be public, but real snapshots, customer documents, private manuals, emails, or PII stay behind tenant privacy boundaries.

### Execution summary (the long-run dashboard contract)

A compact status component for long source-surface runs. It reads the factory path outputs (scan partitions, public-source worker jobs, replay run records, canonical row-family JSONL, load-plan manifest, component-id index) — never source bodies — and reports: curated manifest count from the component-id index; partition count by source surface / risk tier / status / vertical / expected object type; queued and replayed jobs by stage; generated row counts by family; promotion holds/candidates/rejects/review-before-promotion; initial and promotion review-ticket counts; relationship-preflight status and issue count; the bulk load SQL path and command; and the safety boundary (no bodies fetched, no raw private data stored, excluded scopes preserved). The load-bearing rule: never describe curated *manifests* as *objects* — a single generated run may already hold tens of thousands of row-level objects, so manifests (curated catalog definitions) and generated rows (operational objects in Postgres/pgvector/object storage) are always counted separately. For million-object runs this summary lets operators resume incomplete partitions, prioritize review queues, and load only preflight-clean batches.
