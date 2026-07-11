# Staged Versus Committed Load Audit

Generated JSONL row counts are not canonical database counts. A load plan can
prove that rows are staged and preflight-clean, but the platform still needs to
prove that those rows were committed to Postgres and pgvector.

## Inputs

The audit reads:

- a load-plan manifest with staged bulk counts and `load.sql`;
- optional machine-readable rows from `db/postgres/object_count_report.sql`;
- optional execution summary metadata for partition and review context.

If committed Postgres counts are absent, the audit must say `staged_only`
instead of claiming database completion.

## Statuses

- `verified`: committed counts were supplied and every audited relation matches
  the staged count.
- `staged_only`: staged counts exist and the load plan is preflight-clean, but
  committed database counts were not supplied.
- `mismatch`: at least one committed relation count differs from the staged
  load-plan count.

## Relations

The audit checks the canonical high-volume object relations:

- source records;
- normalized objects;
- canonical entities;
- object/entity refs;
- dedupe clusters;
- review tickets;
- promotion decisions;
- index records;
- object embeddings;
- label assignments;
- dimension values.

This lets the product state exactly what is proven: curated manifests,
staged generated rows, or committed canonical database rows.

## Operating Rule

Public dashboards should use committed counts when available. Staged counts are
useful for planning and review queues, but they should be labeled as staged.
Million-object claims require committed counts or a clearly stated storage tier
such as object storage plus verified load manifests.
