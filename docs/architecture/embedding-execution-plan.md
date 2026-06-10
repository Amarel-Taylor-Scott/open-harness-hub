# Embedding Execution Plan

The source-surface factory emits `object_embedding` rows as durable work items before any vector provider is called. The embedding execution plan turns those rows into auditable batches, cost estimates, and completion stubs so vector generation can run locally, through a hosted endpoint, or through a cloud-native vector stack without changing the upstream object factory.

## Why this exists

The catalog is designed to grow from thousands of manifests to millions of generated knowledge objects. Embedding generation is one of the first places where cost, privacy, and operational drift can get out of control. Treating embeddings as planned work items gives us:

- Stable batch IDs for replay, retry, and audit.
- A per-profile cost estimate before provider calls happen.
- A place to enforce local-only routing for private or sensitive text.
- Completion records that can be reconciled against Postgres/pgvector, BigQuery vector indexes, or another vector store.
- A clean boundary between generated objects, vector execution, and search readiness.

## Flow

1. `object-embeddings.jsonl` is emitted by the source-surface row factory.
2. `scripts/db/embedding_execution_plan.py` groups rows by embedding profile.
3. The planner writes:
   - `embedding-batches.jsonl`
   - `embedding-completion-stubs.jsonl`
   - `embedding-execution-plan.json`
4. A later worker uses the batch records to call the selected embedding runtime.
5. Completion rows are updated with vector storage status and reconciled with the committed database.

The planner is intentionally side-effect free. It does not call external APIs, write vectors, or mutate the database.

## Profile Types

`knowledge-pack/embedding-execution-patterns` defines seed profiles for:

- Local sentence-transformer execution for low-cost, private baseline indexing.
- OpenAI-compatible external embedding APIs with run-scoped pricing snapshots.
- Local TEI or vLLM-style embedding services for containerized worker fleets.
- BigQuery-ready vector indexing where embeddings and search live near analytical data.

These profiles are not meant to freeze the platform to one provider. They are routing hints that preserve dimensions, runtime, trust boundary, pricing assumptions, and audit requirements.

## Cost Model

The planner estimates token units from input text and multiplies by profile pricing when a profile has a known price. Local profiles default to zero token price because hardware and queue cost are accounted for separately. External profiles can remain price-unknown until a live pricing snapshot is attached.

This supports a product workflow where a user can ask for the cheapest acceptable pipeline, compare local and hosted embedding options, and understand which privacy boundary or latency tradeoff they are accepting.

## Audit Model

Each planned completion stub starts with:

- `status: planned`
- `vector_stored: false`
- `text_hash`
- `batch_id`
- `profile_id`

That gives later workers enough information to resume safely, detect duplicate work, and compare staged embedding intent with committed vector records.

## Relationship To Search

The embedding execution plan complements the hybrid search design:

- Labels and dimensions support exact filters and faceted browsing.
- BM25 supports keyword recall.
- Embeddings support semantic recall.
- Reranking or polishing models can verify that retrieved objects actually match the user intent.

At million-object scale, the search system should stay hybrid. Pgvector is useful for product search and smaller deployments; BigQuery vector search or partitioned vector services may be better for large analytical scans, batch comparisons, or cost-isolated tenant workloads.
