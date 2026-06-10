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
