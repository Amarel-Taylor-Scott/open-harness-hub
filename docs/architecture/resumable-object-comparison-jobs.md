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
