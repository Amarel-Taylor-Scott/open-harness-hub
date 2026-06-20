# Postgres Load Execution and Audit

The object factory can generate load plans without touching a database. The
next boundary is a deliberate execution plan that applies `load.sql`, exports
committed counts, and feeds those counts back into the staged-versus-committed
audit.

## Execution Shape

The planner is side-effect free. It emits commands for:

1. starting local pgvector when the target is Docker;
2. setting `DATABASE_URL`;
3. initializing `db/postgres/schema.sql`;
4. applying the generated `load.sql`;
5. probing catalog operational views for catalog-manifest bridge loads;
6. running `db/postgres/object_count_report.sql`;
7. converting `psql --csv` count output to JSON;
8. running the staged-versus-committed load audit.

The plan can target local Docker, Render, or another managed Postgres service
that supports pgvector.

## Proof Boundary

There are three count levels:

- curated manifests from the component-id index;
- staged generated rows from JSONL and bulk-load manifests;
- committed canonical rows from Postgres.

Only committed canonical counts prove that a load actually landed in the
database. If no committed count rows are supplied, the audit must remain
`staged_only`.

For catalog-manifest bridge loads, committed counts are not enough by
themselves. The operator plan also runs the read-only
`catalog_operational_view_probe.py` against the target database after
`load.sql` is applied. That probe verifies the catalog dashboard views exist
and have rows before row-backed consumers treat the load as operationally
ready.

## Safety

The generated plan does not contain database credentials. It does not run
Docker or mutate a database. Operators should review the target `DATABASE_URL`
before applying schema or load SQL, then publish the committed-count audit with
the run summary.
