# Vector DB spec — Open Harness Hub

Two indexes:

1. **Catalog index** — one vector per artifact (embedding of
   `name + description + tags`). Powers semantic catalog search and
   "find similar harnesses / pipelines / rule packs" features.
2. **Knowledge index** — one vector per `knowledge_leaf` (embedding of
   the leaf body's text content). Powers RAG retrieval inside pipeline
   execution.

Both indexes are populated by `scripts/db/build_vector_index.py`.

## Index: `oh_catalog`

| Field | Type | Required | Use |
|---|---|---|---|
| `artifact_id`    | string | yes | Primary key. |
| `type`           | string | yes | Filter. |
| `industry`       | array  | no  | Filter. |
| `capability`     | array  | no  | Filter. |
| `modality`       | array  | no  | Filter. |
| `trust_boundary` | string | no  | Filter. |
| `lifecycle`      | string | no  | Filter. |
| `embedding`      | f32[D] | yes | The vector. `D` matches embedder dim. |

Default embedder: `sentence-transformers/all-MiniLM-L6-v2` (D = 384).
Override via `vector.embedder` in `mkdocs.yml` or env var
`OH_EMBEDDER_MODEL`.

## Index: `oh_knowledge`

| Field | Type | Required | Use |
|---|---|---|---|
| `leaf_id`        | string | yes | Primary key. |
| `pack_id`        | string | yes | Filter to a single pack. |
| `leaf_type`      | string | yes | Filter to a leaf type. |
| `language`       | string | no  | Filter. |
| `industry`       | array  | no  | Filter. |
| `chunk_index`    | int    | no  | Sub-chunk order within a leaf. |
| `text`           | string | yes | Original text used for the embedding. |
| `embedding`      | f32[D] | yes | The vector. |

## Backend mapping

| Backend | Index | Native filters | Notes |
|---|---|---|---|
| Pinecone | namespace per index | metadata filter | Managed. |
| Weaviate | class per index | where-filter | Open source. |
| Qdrant   | collection per index | payload filter | Open source. |
| Chroma   | collection per index | metadata filter | Embedded. |
| pgvector | extension on `knowledge_leaf` + `artifact` | SQL WHERE | Same DB as canonical store. Recommended default. |

The pgvector option is the recommended default because it keeps both
the canonical relational store and the vector index in one database,
which removes a class of sync bugs at small/medium scale.

## Refresh policy

The vector indexes are derived. They MUST be regenerated whenever a
manifest changes its embedded text. CI runs the rebuild on every
push to `main` and writes a vector-index checksum into `db/vector/checksum.txt`.
