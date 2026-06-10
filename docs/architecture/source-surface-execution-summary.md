# Source Surface Execution Summary

Long source-surface runs need a compact status component. Operators should be
able to see how many partitions ran, which worker stages executed, how many
generated rows are staged, how many candidates are review-held, and whether the
batch is safe to load into Postgres and pgvector.

## Inputs

The summary reporter reads the outputs of the source-surface factory path:

- scan partitions;
- public-source worker jobs;
- replay run records;
- canonical row-family JSONL;
- load-plan manifest;
- component-id index.

It does not read source bodies. It only summarizes execution metadata, staged
row counts, promotion decisions, review tickets, and load readiness.

## Required Metrics

Every multi-day run should report:

- curated manifest count from the component-id index;
- partition count by source surface, risk tier, status, vertical, and expected
  object type;
- queued and replayed jobs by stage;
- generated row counts by family;
- promotion holds, promotion candidates, rejects, and review-before-promotion
  decisions;
- initial and promotion review-ticket counts;
- relationship preflight status and issue count;
- bulk load SQL path and command;
- safety boundary: no source bodies fetched, no raw private data stored, and
  excluded scopes preserved.

## Why It Matters

The project should never describe `4,216` manifests as `4,216 objects` when a
single generated run may already hold tens of thousands of row-level objects.
The summary keeps the two counts separate:

- manifests are curated catalog definitions;
- generated rows are operational objects that belong in Postgres, pgvector, and
  object storage.

For million-object runs, this summary becomes the dashboard contract. It lets
operators resume incomplete partitions, prioritize review queues, and load only
preflight-clean batches.
