# Database representations

Every artifact in the catalog persists in four representative database
shapes. The canonical store is **PostgreSQL** (`db/postgres/schema.sql`);
the other backends derive from it.

| Backend | Best at | File |
|---|---|---|
| PostgreSQL / SQLite | "Find every harness in industry X with capability Y." | [`db/postgres/schema.sql`](https://github.com/TaylorAmarelTech/open-harness-hub/blob/main/db/postgres/schema.sql) |
| MongoDB / Couchbase / Firestore | "Give me the full manifest of one artifact." | [`db/mongodb/collections.md`](https://github.com/TaylorAmarelTech/open-harness-hub/blob/main/db/mongodb/collections.md) |
| Redis / DynamoDB | Runtime cache + ephemeral run state. | [`db/redis/keys.md`](https://github.com/TaylorAmarelTech/open-harness-hub/blob/main/db/redis/keys.md) |
| Pinecone / Weaviate / Qdrant / Chroma / pgvector | Catalog semantic search + RAG retrieval. | [`db/vector/spec.md`](https://github.com/TaylorAmarelTech/open-harness-hub/blob/main/db/vector/spec.md) |

## The row shape every backend agrees on

```sql
-- One row per artifact.
artifact(id, type, version, name, description, license, lifecycle,
         trust_boundary, freshness, created, updated, attribution,
         links, body /* full manifest as JSONB */)

-- Join tables for cross-cutting axes.
artifact_industry(artifact_id, industry)
artifact_capability(artifact_id, capability)
artifact_modality(artifact_id, modality)
artifact_tag(artifact_id, tag)

-- Edges between artifacts (consumes / emits / step_ref / rubric / ...).
artifact_ref(src_id, dst_id, role)

-- Leaves inside rule packs and knowledge packs.
rule(rule_id, pack_id, family, severity, category, pattern, body, enabled)
knowledge_leaf(leaf_id, pack_id, leaf_type, industry, language, body)

-- Pipeline / benchmark / harness runs.
run(run_id, artifact_id, started_at, finished_at, status, adapter_id,
    inputs, outputs, trace, cost_usd, trust_boundary)
```

Most deployments use **two** backends: PostgreSQL + pgvector
(or PostgreSQL + Pinecone/Weaviate). Redis is a nice-to-have for
high-throughput hosted catalogs.
