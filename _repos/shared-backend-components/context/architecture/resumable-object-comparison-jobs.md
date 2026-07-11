# Resumable Object Comparison Jobs

At million-object scale, naive `n x m` comparison is not operationally usable.
The registry needs blocked, resumable pairwise comparison jobs so workers can
compare only plausible object pairs, checkpoint completed leaves, and resume
without repeating prior work.

## Job Model

The comparison system emits four job-control row families:

- `comparison_job`: the parent job, block fields, total pair count, skipped
  completed pairs, and remaining pair count;
- `comparison_block`: a blocking key such as object type, jurisdiction,
  privacy boundary, publisher, label path, or embedding bucket;
- `comparison_leaf`: a small shard of pair keys that one worker can process;
- `comparison_checkpoint`: completed pair keys and leaf status.

Comparison results are additive. A worker can process one leaf, write result and
checkpoint JSONL, then stop. The next run loads checkpoints and excludes already
completed pairs.

## Blocking Strategy

Blocking should start cheap and become more selective:

1. deterministic fields: object type, jurisdiction, privacy boundary, source
   publisher, label path;
2. semantic buckets: embedding centroid, model-generated dimension, topic,
   procedure family;
3. freshness windows: effective date, retrieved date, supersession chain;
4. risk partitions: high-impact objects can use smaller leaves and stricter
   human-review thresholds.

This avoids comparing every object to every other object while still supporting
deep duplicate, conflict, supersession, and near-neighbor analysis.

## Resume Semantics

Each pair key is stable: `min(object_id)::max(object_id)`. Checkpoints store
completed pair keys, so retries are idempotent. Leaf workers can be spread
across local processes, Render workers, Cloud Run jobs, or queue consumers.

The first implementation is intentionally local and JSONL-based. It can later be
backed by Postgres tables, BigQuery batch jobs, or a distributed queue without
changing the logical job contract.

## Hybrid comparison blocking (consolidated)

> Folds the durable design of the merged hybrid-comparison-blocking plan — how the comparison planner enriches objects and blocks pairs before lexical/embedding/model comparison.

The comparison planner accepts normalized objects plus optional row families (`label_assignment`, `dimension_value`, `object_entity_ref`, `object_embedding`), enriches the objects with comparison metadata, and creates leaf-sharded pair plans (`comparison-jobs.jsonl`, `comparison-blocks.jsonl`, `comparison-leaves.jsonl`, `comparison-records.jsonl`). Two blocking modes: **`all`** keeps strict behavior — every configured block field must match in one compound key (useful for strict privacy/tenant boundaries); **`any`** lets any configured field propose a candidate pair (a shared embedding bucket, entity, label path, or object type creates a block), with pair keys deduplicated globally so the same pair is never compared twice even when many evidence routes propose it. Recommended million-object policy: use strict fields first (tenant/privacy boundary, object type, source trust tier), then additive fields (`embedding_bucket`, `entity_ids`, `label_paths`, `risk_tier`, required-stage entities, output-type entities) — at high volume, run separate jobs per tenant/privacy boundary and use `any` mode inside each partition, isolating sensitive records while still using hierarchy and graph signals for recall. Leaf workers compare enriched records and checkpoint completed pair keys; restarted jobs skip completed pairs even when a pair is proposed by multiple block keys.
