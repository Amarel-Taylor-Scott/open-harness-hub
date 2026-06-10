# Object embedding batch loader

*tool* · `tool/object-embedding-batch-loader` · v0.1.0 · experimental

Loads object_embedding rows into the pgvector-enabled Postgres store defined
in db/postgres/schema.sql. Reads a JSONL file of pre-computed embedding
work items (subject_id, subject_type, embedding_model, text, text_hash,
embedding vector) and issues deterministic UPSERT SQL targeting the
object_embedding table with its UNIQUE constraint on
(subject_id, subject_type, embedding_model, text_hash).

Validates that the vector dimension of each row matches the declared schema
dimension before loading. Rows with mismatched dimensions, missing required
fields, or NULL embeddings are routed to a rejected JSONL sidecar with
reasons, ensuring only structurally complete embeddings reach the store.
Emits a load audit summary with accepted/rejected counts per embedding model.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | embedding, retrieval, serving, governance |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



