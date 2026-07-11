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

## Execution stages (consolidated)

> Folds the durable design of the merged embedding plans — daily embedding execution, the local hash embedding worker, the pgvector load plan, the committed-load audit, and the vector readiness audit. Frozen per-run sample counts live in the archived source docs; the stage contracts below are the durable part.

The plan above defines *intent*. These stages turn intent into stored, audited vectors. Every stage is side-effect free unless it explicitly applies SQL: each writes review evidence and operator commands, and never mutates a database on its own.

### Stage 1 — Daily embedding execution (`scripts/db/daily_embedding_execution_batch_plan`)

Daily component generation produces `object_embedding` rows as work orders, not stored vectors. This planner turns the work rows into retryable batches, records model profiles and costs, and runs a first vector-readiness pass. It emits `embedding-model-profiles.json`, `embedding-plan/embedding-batches.jsonl`, `embedding-plan/embedding-completion-stubs.jsonl`, `embedding-plan/embedding-execution-plan.json`, `vector-readiness/vector-readiness-summary.json`, and a batch-plan summary. It does not call providers, write vectors, or touch Postgres — workers (local, Render, Cloud Run, or hosted API) do that and must write stored-vector metadata for the readiness audit. Replace hosted placeholder pricing with a live pricing snapshot before any external execution.

### Stage 2 — Local hash embedding worker (`scripts/db/local_hash_embedding_worker`)

The first executable vector-producing worker. It reads an execution plan, joins planned completion rows back to source `object_embedding` text, generates deterministic fixed-dimension vectors, and writes pgvector-ready JSONL (`completed-embedding-rows.jsonl`, `stored-vector-rows.jsonl`, a readiness summary, and a worker summary). It is deliberately dependency-free — no model download, provider, or network — giving an immediate replayable vector path while production semantic workers are selected. Each stored vector row carries: `embedding_id`, `subject_id`, `subject_type`, `batch_id`, `profile_id`, `text_hash`, `dimensions`, `vector`, `worker_id`, `storage_backend`, `embedding_runtime`, `embedding_model`. Quality boundary: hash vectors validate orchestration, row contracts, load shape, replay, and readiness — they are NOT a final semantic model. Production workers (sentence-transformers, TEI, vLLM, hosted APIs, BigQuery) reuse the same completion + stored-vector row contract.

### Stage 3 — Pgvector embedding load plan (`scripts/db/pgvector_embedding_load_plan`)

Converts stored-vector JSONL into reviewable SQL for the canonical `object_embedding` table — the bridge between workers and Postgres+pgvector. It joins original text back by `embedding_id` (the table stores both `text` and `embedding`), against the canonical schema dimension. Emits `object-embedding-load.sql`, accepted/rejected row evidence, and a summary. Rows are rejected before SQL emission when: the embedding id is missing; the vector is missing; the vector length disagrees with row dimensions; row dimensions do not match the canonical schema dimension; or source text cannot be joined by embedding id. Operators then apply `schema.sql` + `object-embedding-load.sql` via `psql`, keeping JSONL as the safe review/replay layer and Postgres+pgvector as the canonical product store.

### Stage 4 — Embedding committed-load audit (`scripts/db/embedding_committed_load_audit`)

The final side-effect-free readiness gate before vector search is called product-ready. It compares four layers: planned completion rows, stored-vector readiness rows, pgvector load-plan accepted/rejected rows, and committed Postgres `object_embedding` counts — so JSONL evidence is never mistaken for live product data. Before SQL is applied it reports `audit_status: load_planned_not_committed`, `vector_search_product_ready: false`; once committed counts cover the accepted load rows it returns `audit_status: verified`, `vector_search_product_ready: true`.

### Stage 5 — Vector readiness audit

Keeps "planned work" and "searchable vectors" as separate states so a pipeline never claims semantic-search readiness merely because embedding work was planned (part of the [north star platform architecture](north-star-platform-architecture.md)). It is metadata-only — comparing ids, hashes, dimensions, and status flags — and never needs raw source text, never calls providers, and never writes a database. It emits `vector-readiness-summary.json`, `vector-readiness-rows.jsonl`, and `vector-orphan-rows.jsonl`, classifying each row ready / missing / present-but-not-stored / needs-review (review = text-hash or dimension mismatch). This is what lets the registry answer, provider-neutrally and for cost control, which objects have planned embeddings, which have stored vectors, which are stale or mismatched, which stored vectors are orphans, and which batches are safe to retry. Private or sensitive text stays behind the embedding profile's trust boundary; a vector that cannot be verified without exposing raw text is routed for local review instead of exported.

> Two additional smoke/contract variants — a local embedding worker contract and a local pgvector embedding smoke plan — are archived alongside the merged sources; both only prove shape / audit compatibility and are superseded by the worker + load-plan + audit stages above.
