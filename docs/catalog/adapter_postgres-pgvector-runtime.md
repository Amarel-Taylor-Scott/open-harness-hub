# Postgres + pgvector canonical store adapter

*adapter* · `adapter/postgres-pgvector-runtime` · v0.1.0 · experimental

Provider-neutral adapter for the Open Harness Hub canonical Postgres store with
pgvector extension enabled. Wraps all read/write paths for the component,
normalized_object, object_embedding, index_record, source_record,
component_change_event, and related tables defined in db/postgres/schema.sql.

Supports local Docker, Render Postgres, Supabase, Google Cloud SQL, and any
libpq-compatible endpoint via the DATABASE_URL environment variable. The
vector(384) dimension baseline matches the local MiniLM embedding worker;
deployments using larger models add parallel embedding rows without changing
the schema.

Does not hardcode connection strings, pool sizes, or vector dimensions — all
are resolved at runtime from environment or caller config.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | retrieval, serving, embedding, governance |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



