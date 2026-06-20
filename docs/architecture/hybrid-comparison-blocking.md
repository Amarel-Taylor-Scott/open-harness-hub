# Hybrid Comparison Blocking

Object comparison should use every cheap signal available before doing lexical,
embedding, or model-assisted comparison. The comparison planner now accepts
normalized objects plus optional row families:

- `label_assignment`
- `dimension_value`
- `object_entity_ref`
- `object_embedding`

The planner enriches normalized objects with comparison metadata and then
creates leaf-sharded pair plans.

## Blocking Modes

`all` mode keeps the old behavior: every configured block field must match in a
single compound key. This is useful for strict privacy or tenant boundaries.

`any` mode lets any configured field propose a candidate pair. A shared
embedding bucket, shared entity, shared label path, or shared object type can
create a block. Pair keys are deduplicated globally, so the same pair can appear
through many evidence routes without being compared repeatedly.

## Recommended Million-Object Policy

Use strict fields first:

- tenant or privacy boundary;
- object type;
- source trust tier.

Then use additive fields:

- `embedding_bucket`;
- `entity_ids`;
- `label_paths`;
- `risk_tier`;
- required-stage entities;
- output-type entities.

At high volume, run separate jobs by tenant/privacy boundary, then use `any`
mode inside each partition. This keeps sensitive records isolated while still
using flexible hierarchy and graph signals for recall.

## Worker Semantics

The planner writes:

- `comparison-jobs.jsonl`
- `comparison-blocks.jsonl`
- `comparison-leaves.jsonl`
- `comparison-records.jsonl`

Leaf workers compare enriched records and checkpoint completed pair keys.
Restarted jobs skip completed pairs even if the pair is proposed by multiple
block keys.
