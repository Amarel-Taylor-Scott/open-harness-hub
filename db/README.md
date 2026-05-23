# Database mappings — Open Harness Hub

Every Open Harness Hub manifest persists in the database shape of your
choice. The **canonical schema is PostgreSQL** (`postgres/schema.sql`);
the other backends derive from it.

| Backend | Workload it shines at | File |
|---|---|---|
| **PostgreSQL** | Canonical store. Relational with JSONB for the long tail. | `postgres/schema.sql` |
| **SQLite** | Embedded / single-file portable catalog. WAL mode + FTS5 built-in. | `sqlite/schema.sql` |
| **SQLite + sqlite-vec** | Embedded vector search — single-file catalog + vectors, zero deps. | `sqlite-vec/schema.sql` |
| **DuckDB** | OLAP analytics over runs / cost / latency without a server. Native ARRAY + JSON + HNSW. | `duckdb/schema.sql` |
| **MongoDB / Couchbase / Firestore** | Document store. One collection per artifact type. | `mongodb/collections.md` |
| **Redis / DynamoDB** | Runtime cache + ephemeral run state. Sub-ms reads. | `redis/keys.md` |
| **Elasticsearch / OpenSearch** | BM25 + dense vector hybrid search at scale (Reciprocal Rank Fusion). | `elasticsearch/index-templates.md` |
| **Neo4j / Memgraph** | Graph queries: which pipelines depend on this harness? 2-hop blast radius? | `neo4j/schema.cypher` |
| **BigQuery** | Warehouse-scale catalog evolution + run analytics. ARRAY/STRUCT-native. | `bigquery/schema.sql` |
| **Pinecone / Weaviate / Qdrant / Chroma / pgvector** | Vector-only stores for RAG retrieval + catalog semantic search. | `vector/spec.md` |

## Which to pick

The five-question decision tree:

1. **Do you need to embed the catalog inside a desktop or mobile app?**
   → **SQLite** (`sqlite/`) plus **sqlite-vec** for vector search.
2. **Are you running ad-hoc analytical queries (cost, latency, lineage)?**
   → **DuckDB** for laptop-scale, **BigQuery** at warehouse scale.
3. **Is RAG retrieval the dominant workload?**
   → **Elasticsearch / OpenSearch** for BM25 + RRF hybrid, or a
   pure vector store from `vector/spec.md`.
4. **Are you tracing dependency graphs across the catalog (pipelines
   that depend on a harness, blast radius of a deprecation)?**
   → **Neo4j / Memgraph**.
5. **Otherwise**: **PostgreSQL** (with optional **pgvector**) is the
   default — relational queries, JSONB for the long tail, vector
   index in the same database.

Most real deployments combine **two**: PostgreSQL or SQLite as the
canonical store, plus one specialty engine for either RAG retrieval
(Elasticsearch / vector DB) or analytics (DuckDB / BigQuery).

## Row shape every backend agrees on

```sql
-- One row per artifact (with JSON body for the long tail).
artifact(id, type, version, name, description, license, lifecycle,
         lifecycle_position, trust_boundary, freshness, eu_ai_act_risk,
         created, updated, attribution, links, body)

-- Cross-cutting axes
artifact_industry(artifact_id, industry)
artifact_capability(artifact_id, capability)
artifact_modality(artifact_id, modality)
artifact_tag(artifact_id, tag)

-- Inter-artifact edges
artifact_ref(src_id, dst_id, role)

-- Leaves inside packs
rule(rule_id, pack_id, family, severity, category, pattern, body, enabled)
knowledge_leaf(leaf_id, pack_id, leaf_type, industry, language, body, embedding)

-- Pipeline / benchmark / harness runs
run(run_id, artifact_id, started_at, finished_at, status, adapter_id,
    inputs, outputs, trace, cost_usd, trust_boundary)
```

The DuckDB and BigQuery variants flatten the cross-cutting axes into
native ARRAY columns; SQLite uses the join tables; document stores
store everything nested. The query model stays the same.

## Loaders (planned)

`scripts/db/`:

- `load_postgres.py`
- `load_sqlite.py`
- `load_duckdb.py`
- `load_mongodb.py`
- `load_elasticsearch.py`
- `load_neo4j.py`
- `load_bigquery.py`
- `build_vector_index.py` ✅ (already shipped — emits both `oh_catalog.jsonl` and `oh_knowledge.jsonl` for any vector backend)

Each loader is idempotent: rerunning updates rows by `id` rather than
inserting duplicates.
