# Promotion Index Deltas

Promotion decisions should update search and quality indexes incrementally. A factory may score millions of candidate primitives, but only a small subset will become curated manifests. The decisions still need to be searchable by score, risk, review status, output type, and cost/deployment value.

## Flow

```text
normalized candidate objects
-> promotion scoring
-> promotion-decision JSONL
-> promotion index deltas
-> quality/facet/cost indexes
-> replay audit
```

## Index Kinds

- `quality`: score, decision, review reasons, and promotion readiness.
- `facet`: risk flags, recommended outputs, decision category, and source family.
- `cost`: cost-savings, economic value, and deployment-management value criteria.

## Why This Matters

At one million objects, promotion scoring cannot trigger a full search rebuild. The promotion delta emitter writes a partition manifest and replayable index deltas so the platform can update only affected index partitions.

The output can be consumed by the partition registry replay audit to prove that candidate scoring produced deterministic index state.
