# Primitive platform backend

The hosted product needs a backend that behaves more like a search, package, and build platform than a static documentation site.

The static catalog remains useful for curated manifests. The SaaS backend should manage the larger primitive database: millions of candidate primitives, source records, embeddings, tags, ratings, usage telemetry, verified-source updates, generated blueprints, and multimodal assets.

## Core Services

| Service | Responsibility |
|---|---|
| API gateway | Auth, tenancy, rate limits, request logging, public/private API keys |
| Primitive registry | Canonical metadata for primitives, versions, dependencies, licenses, trust boundaries |
| Source ingest | Routine source scans, verified publisher intake, dedupe, license checks |
| Object factory workers | Dedicated source ingest, page-to-Markdown, digest, privacy gate, LLM polish, verification, labeling, dedupe, cost, and publish-review jobs |
| Embedding service | Batch and streaming embeddings for components, source records, examples, and media captions |
| Keyword search | Exact search over names, identifiers, tags, laws, model names, source URLs, fields |
| Vector search | Semantic retrieval over primitive descriptions, examples, source summaries, and user tasks |
| Graph service | Dependency graph across primitives, pipelines, tools, datasets, rubrics, laws, deployments |
| Query planner | Converts user problem statements into constraints, capabilities, source needs, and search queries |
| Ranker | Combines keyword, vector, graph, usage, rating, cost, freshness, and trust signals |
| Label and dimension service | Assigns hierarchical labels, schema.org-style labels, tenant custom labels, and generated dimensions for hybrid search |
| Model router | Selects local, hosted, cloud, or specialist models by task, modality, cost, latency, trust boundary, and quality tier |
| Blueprint generator | Emits pipeline manifests, runtime files, Terraform/container plans, eval suites, MCP setup plans |
| Eval service | Runs baselines, regression tests, red-team tests, and human review queues |
| Cost service | Active model, media, embedding, storage, vector DB, queue, GPU, and human-review estimates |
| Telemetry service | Usage, ratings, failed runs, forks, deploys, cost traces, model swaps |
| Asset service | Stores generated images, video, audio, thumbnails, transcripts, captions, hashes, provenance |
| Moderation/safety service | Screens text, images, audio, video, prompts, source content, and generated outputs |

## Storage Layout

Use different storage layers for different durability and query needs:

| Layer | Suggested backend | Stores |
|---|---|---|
| Relational DB | Postgres | primitive metadata, versions, tenants, ratings, usage, jobs, source records |
| Vector DB | pgvector initially, Qdrant/Weaviate/Pinecone at scale | component vectors, knowledge vectors, source vectors, media caption vectors |
| Search engine | Postgres FTS initially, OpenSearch/Meilisearch/Typesense at scale | keyword/facet search |
| Graph store | Postgres edges initially, Neo4j/AGE/graph index later | dependencies, alternatives, derived-from, supersedes, deployed-with |
| Object storage | S3/R2/GCS/Azure Blob | raw source snapshots, JSONL batches, generated assets, thumbnails, eval components |
| Queue | Redis/SQS/PubSub/Kafka | scan jobs, embedding jobs, eval runs, media jobs, pricing refresh |
| Warehouse | ClickHouse/BigQuery/Snowflake | telemetry, cost traces, aggregate usage, search analytics |

## Indexes

At million-primitive scale, every primitive should generate multiple index records:

- `keyword_document`: name, aliases, ids, tags, source titles, exact fields.
- `embedding_document`: task, description, examples, constraints, failure modes.
- `facet_record`: industry, capability, modality, jurisdiction, trust boundary, license, deployment target.
- `graph_edges`: uses, requires, replaces, derived_from, compatible_with, deployed_with.
- `quality_record`: rating, eval scores, usage, failure rate, verification status.
- `freshness_record`: source timestamp, effective date, last verified date, deprecation status.
- `cost_record`: expected tokens, calls, GPU seconds, storage, egress, human review.
- `label_record`: hierarchical label, schema.org-style label, tenant custom label, or generated label.
- `dimension_record`: numeric or categorical ranking/routing feature such as complexity, evidence requiredness, cost sensitivity, freshness volatility, or model-swap value.

Before those records are emitted, raw sources should pass through a normalization layer:

- `source_record`: source URL, publisher, license, trust tier, content hash, archive URL, and collection metadata.
- `extracted_object`: task, question, fact, checklist item, decision gate, tool dependency, workflow node, or candidate primitive.
- `entity_mention`: detected entities and source spans.
- `canonical_entity`: linked entity with aliases, registry identifiers, and confidence.
- `dedupe_cluster`: near-duplicate objects grouped by exact ids, fuzzy strings, hashes, vectors, and entity overlap.
- `review_ticket`: reason a human, publisher, legal, safety, or domain expert should review an object.

Use cheap deterministic passes first: exact identifiers, normalized text, trigram/fuzzy matching, SimHash/MinHash, and entity overlap. Use vector similarity and LLM adjudication only after cheaper filters narrow the candidate set.

## Search Flow

```text
user task
-> query planner
-> keyword search
-> label and dimension filters
-> vector search
-> graph expansion
-> policy/license/trust filters
-> ranker
-> blueprint generator
-> cost/eval/deployment bundle
```

For large-scale ingestion, the parallel source flow is:

```text
source surface
-> source governance router
-> object factory job router
-> page-to-markdown/document conversion
-> sensitive data gate
-> LLM polish/verification worker
-> extraction normalizer
-> entity recognition/linking
-> fuzzy dedupe clusterer
-> index record emitter
-> keyword/vector/graph/facet/freshness/quality indexes
-> review queues
```

The vector layer should not carry the whole retrieval burden. Exact labels, schema.org-style types, tenant dimensions, entity links, and model-generated dimension scores should remain first-class index records so search stays explainable and cheap.

For worker-level details, see [Object factory worker fleet](object-factory-worker-fleet.md).

The ranker should explain why components were chosen:

- exact source match.
- semantically similar prior pipeline.
- high verified-source trust.
- strong eval score.
- common deployment pattern.
- cheaper model/runtime option.
- easier model/provider swap.
- lower maintenance burden.

## Multimodal Expansion

The platform should not be text-only. It should support generation and evaluation primitives for:

- text
- image
- video
- audio
- music
- 3D assets
- multimodal documents

Multimodal primitives need extra backend support:

- object storage for large outputs.
- thumbnails, waveform previews, transcripts, captions, and scene summaries.
- perceptual hashes and duplicate detection.
- output safety screening for NSFW, IP, likeness, watermark, malware, hidden text, and policy violations.
- media-specific cost models such as resolution, duration, frames, samples, GPU seconds, and storage.
- provenance for prompts, seeds, model versions, source assets, and licenses.
- review UI for side-by-side media comparison.

## Media Primitive Metadata

```yaml
media_type: image | video | audio | music | 3d | document
generation_mode: text_to_media | media_to_media | edit | upscale | caption | classify | safety_screen
duration_seconds: number
resolution: string
sample_rate: integer
frame_rate: number
style_rights: string
likeness_policy: string
source_asset_refs:
  - string
output_asset_ref: string
preview_asset_ref: string
perceptual_hash: string
safety_checks:
  - string
cost_dimensions:
  - gpu_seconds
  - storage_gb
  - egress_gb
  - model_call
```

## Backend Deployment Shape

Start simple:

- Postgres + pgvector for canonical data and semantic search.
- Redis for queues and caching.
- S3-compatible object storage for source snapshots and generated media.
- Worker containers for scans, embeddings, evals, and media generation.
- Provider-neutral object factory workers for Markdown conversion, privacy screening, LLM polishing, verification, labels, dedupe, indexing, cost metering, and publish review.
- OpenTelemetry-compatible traces.
- Terraform modules for each deployment target.

Scale later:

- split vector search to Qdrant/Weaviate/Pinecone.
- split keyword search to OpenSearch/Typesense.
- move telemetry to ClickHouse.
- use Kubernetes or batch workers for heavy media generation and embedding jobs.
- shard by tenant, modality, source type, or lifecycle stage.

## Required Backend APIs

- `POST /search`: task-to-primitive search.
- `POST /blueprints`: generate deployable pipeline bundle.
- `POST /sources/scan`: run source-surface scan.
- `POST /publishers/intake`: verified source submission.
- `POST /embeddings/jobs`: embed or re-embed primitive batches.
- `POST /evals/runs`: run baseline or regression evals.
- `POST /assets/generate`: generate image/video/audio/music assets.
- `POST /assets/screen`: safety-screen generated or uploaded media.
- `GET /primitives/{id}`: primitive detail with versions, evals, usage, dependencies.
- `GET /primitives/{id}/deployments`: common deployment patterns and cost traces.

## Operational Requirements

- Every index record must be reproducible from a source record or curated manifest.
- Every generated blueprint must carry pricing snapshot ids and assumptions.
- Every verified-source item must carry publisher, signature or review method, effective date, source URL, and content hash.
- Every media output must carry prompt, model, seed when available, safety checks, and license/provenance metadata.
- Every primitive can be deprecated, superseded, forked, rated, and benchmarked.
