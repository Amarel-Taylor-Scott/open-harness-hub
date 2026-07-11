# SaaS operating platform

This platform needs to host a large primitive database, a search/build experience, and a cost-aware execution layer. The first target is not one million curated YAML files. The target is one million indexed primitive records with a smaller curated layer promoted into stable curated components.

## Product Capabilities

| Capability | Backend requirements |
|---|---|
| Login and tenant management | auth provider, orgs, workspaces, roles, API keys, service accounts |
| Payment and plans | subscriptions, usage-based billing, invoices, credits, spending limits |
| Primitive search | keyword search, vector search, facets, graph expansion, source filters |
| LLM-polished results | query rewriting, result explanation, reranking, gap detection, blueprint summary |
| Pipeline generation | component builder, tool/If Statement/eval selection, Terraform/container/runtime emitters |
| Cost estimation | model pricing, cloud pricing, vector index cost, media generation cost, human review |
| Verified publishing | publisher identity, signatures, source hashes, review queues, effective dates |
| Ratings and telemetry | usage, stars, forks, deploys, failures, eval results, reviews, common deployments |
| Multimodal generation | media routing, asset storage, previews, safety screening, provenance |
| Enterprise deployment | private indexes, BYO cloud, VPC, air-gapped export, audit logs |

## Suggested Container Topology

Start with small, cheap containers that scale independently:

| Container | Purpose |
|---|---|
| `web-app` | user UI, dashboard, primitive detail pages, blueprint builder |
| `api` | REST/GraphQL API, auth checks, tenant routing |
| `search-api` | keyword/vector/graph search orchestration |
| `ranker` | hybrid ranking, rating signals, cost-aware ordering |
| `llm-polisher` | Gemma or other small model for query rewrite, result explanations, blueprint summaries |
| `ingest-worker` | source scans, verified publisher intake, normalization |
| `embedding-worker` | batch embeddings and re-embedding jobs |
| `eval-worker` | baseline tests, regression tests, Action scoring |
| `blueprint-worker` | pipeline, Terraform, container, MCP, and runtime generation |
| `pricing-worker` | active pricing snapshots and cost model refresh |
| `media-worker` | image/video/audio/music generation and post-processing |
| `safety-worker` | text and media safety checks |
| `billing-worker` | metering aggregation, invoice sync, quota enforcement |

The cheap default deployment can run most workers on CPU with autoscaling-to-zero. GPU workers should be isolated to media generation, heavy reranking, or local model inference.

## Core Data Model

Important tables or collections:

- `tenants`
- `users`
- `memberships`
- `api_keys`
- `plans`
- `subscriptions`
- `metered_events`
- `spend_limits`
- `primitives`
- `primitive_versions`
- `primitive_embeddings`
- `primitive_tags`
- `primitive_edges`
- `primitive_ratings`
- `primitive_usage_stats`
- `source_surfaces`
- `source_records`
- `publisher_accounts`
- `verified_source_records`
- `search_queries`
- `blueprints`
- `pipeline_runs`
- `eval_runs`
- `pricing_snapshots`
- `media_assets`
- `audit_events`

## Search Stack

The search system should be hybrid:

1. **Keyword**: exact terms, IDs, source names, statutes, standards, tags, providers.
2. **Vector**: semantic similarity over task, examples, descriptions, source summaries.
3. **Graph**: dependencies, alternatives, compatible models, deployment edges.
4. **Facets**: industry, capability, modality, jurisdiction, trust boundary, license, deployment target.
5. **Ratings**: eval score, usage, success rate, common deployments, recency.
6. **LLM polishing**: explain and refine the final result set.

The LLM polishing layer should be small and cheap by default. Gemma-class or other efficient local/open models are appropriate for:

- query rewrite.
- deduplicating similar result groups.
- explaining why a primitive matches.
- summarizing tradeoffs.
- detecting missing components in a proposed pipeline.
- drafting the final blueprint narrative.

Do not use the polishing model as the source of truth. It explains ranked search results; it does not replace retrieved evidence, ratings, evals, or verified-source records.

## Billing And Metering

Meter events at the primitive and platform level:

| Event | Metering unit |
|---|---|
| search query | query count, result count, LLM polishing tokens |
| vector search | embedding count, vector reads |
| source scan | source records scanned, browser minutes, API calls |
| embedding job | records embedded, tokens, model/provider |
| blueprint generation | generated files, LLM tokens, tool calls |
| eval run | examples scored, judge tokens, human-review minutes |
| media generation | image count, video seconds, audio seconds, GPU seconds |
| asset storage | GB-month, egress |
| verified publishing | records submitted, records verified, update frequency |

Each tenant should have:

- monthly included credits.
- hard and soft spend limits.
- per-worker quotas.
- per-source scan limits.
- BYO provider keys option.
- cost simulator before expensive runs.

## Deployment Phases

### Phase 1: Low-cost MVP

- Postgres + pgvector.
- Postgres full-text search or Typesense.
- S3-compatible object storage.
- Redis queue.
- CPU workers.
- Gemma-class local polishing model through Ollama or vLLM.
- Stripe or equivalent billing.
- Auth.js, Clerk, Supabase Auth, or cloud-native identity.

### Phase 2: Scale Search

- Dedicated vector DB if pgvector becomes limiting.
- OpenSearch/Typesense for larger keyword/facet search.
- ClickHouse for telemetry and search analytics.
- separate graph service or graph extension.
- batch embedding workers with spot/preemptible nodes.

### Phase 3: Enterprise And Multimodal

- private tenant indexes.
- BYO cloud deployment.
- Kubernetes/GKE/EKS/AKS support.
- GPU media workers.
- signed verified-source publishing.
- audit export.
- air-gapped primitive bundles.

## Cost Controls

To stay cheaper than cloud-native agent platforms:

- use CPU-first workers.
- cache search, embeddings, pricing snapshots, and blueprint candidates.
- batch embeddings.
- use local small models for polishing.
- allow BYO model and BYO cloud.
- keep generated media workers separate and quota-limited.
- promote high-use primitives into precomputed indexes.
- store raw source snapshots in cheap object storage.
- reserve expensive frontier calls for final blueprint generation or evals.

## Why This Beats A Generic Agent Builder

A generic agent builder asks users to configure an agent.

This platform should let users describe a problem, then use the primitive database to assemble:

- the right tools.
- the right rules.
- the right examples.
- the right evals.
- the right deployment shape.
- the right cost profile.
- the right model/provider abstraction.

The backend exists to make that search and assembly loop fast, trusted, and economically sane.

## Backend services, storage, and index detail (consolidated)

> Folds the durable design of the merged primitive-platform-backend plan — the fuller service catalog, storage layout, per-primitive index records, the normalization layer, search flow, multimodal support, and the backend API + operational contract. Vocabulary is normalized to the seven-primitive model (an Action covers what legacy notes called a persona/tool/processor/harness/rubric).

The hosted product behaves like a search + package + build platform, not a static documentation site. The static catalog stays useful for curated components; the backend manages the larger primitive database — millions of candidate primitives, source records, embeddings, tags, ratings, usage telemetry, verified-source updates, generated blueprints, and multimodal assets.

### Core services

API gateway (auth, tenancy, rate limits, request logging, public/private API keys); primitive registry (canonical metadata, versions, dependencies, licenses, trust boundaries); source ingest (routine scans, verified-publisher intake, dedupe, license checks); object-factory workers (source ingest, page-to-Markdown, digest, privacy gate, LLM polish, verification, labeling, dedupe, cost, publish-review); embedding service; keyword search; vector search; graph service (dependency graph across primitives, pipelines, tools, datasets, Actions, laws, deployments); query planner (problem statement → constraints / capabilities / source needs / queries); ranker (keyword + vector + graph + usage + rating + cost + freshness + trust); label & dimension service; model router (local/hosted/cloud/specialist by task, modality, cost, latency, trust boundary, quality tier); blueprint generator (pipeline components, runtime files, Terraform/container plans, eval suites, MCP setup); eval service; cost service; telemetry service; asset service; moderation/safety service.

### Storage layout (durability / query split)

Relational DB (Postgres) — primitive metadata, versions, tenants, ratings, usage, jobs, source records; vector DB (pgvector → Qdrant/Weaviate/Pinecone at scale); search engine (Postgres FTS → OpenSearch/Meilisearch/Typesense); graph store (Postgres edges → Neo4j/AGE/graph index); object storage (S3/R2/GCS/Azure Blob — raw snapshots, JSONL batches, assets, thumbnails); queue (Redis/SQS/PubSub/Kafka); warehouse (ClickHouse/BigQuery/Snowflake — telemetry, cost traces, aggregate usage, search analytics).

### Per-primitive index records

At million-primitive scale each primitive generates multiple index records: `keyword_document`, `embedding_document`, `facet_record`, `graph_edges`, `quality_record`, `freshness_record`, `cost_record`, `label_record`, `dimension_record`. Before those are emitted, raw sources pass a normalization layer: `source_record`, `extracted_object`, `entity_mention`, `canonical_entity`, `dedupe_cluster`, `review_ticket`. Use cheap deterministic passes first (exact ids, normalized text, trigram/fuzzy, SimHash/MinHash, entity overlap); use vector similarity and LLM adjudication only after cheap filters narrow the set. The vector layer should not carry the whole retrieval burden — exact labels, schema.org-style types, tenant dimensions, entity links, and model-generated dimension scores stay first-class index records so search stays explainable and cheap.

### Search flow and parallel ingestion flow

Retrieval: user task → query planner → keyword search → label/dimension filters → vector search → graph expansion → policy/license/trust filters → ranker → blueprint generator → cost/eval/deployment bundle. Ingestion: source surface → source-governance router → object-factory job router → page-to-Markdown → sensitive-data gate → LLM polish/verification → extraction normalizer → entity recognition/linking → fuzzy dedupe → index-record emitter → keyword/vector/graph/facet/freshness/quality indexes → review queues. The ranker explains its choices (exact source match, semantically similar prior pipeline, high verified-source trust, strong eval score, common deployment pattern, cheaper model/runtime, easier provider swap, lower maintenance).

### Multimodal support

Not text-only: text, image, video, audio, music, 3D, multimodal documents. Extra backend support: object storage for large outputs; thumbnails / waveforms / transcripts / captions / scene summaries; perceptual hashes + duplicate detection; output safety screening (NSFW, IP, likeness, watermark, malware, hidden text, policy); media-specific cost models (resolution, duration, frames, samples, GPU seconds, storage); provenance (prompts, seeds, model versions, source assets, licenses); side-by-side media review UI. Media primitive metadata carries `media_type`, `generation_mode`, duration/resolution/sample_rate/frame_rate, `style_rights`, `likeness_policy`, source/output/preview asset refs, `perceptual_hash`, `safety_checks`, and `cost_dimensions` (gpu_seconds, storage_gb, egress_gb, model_call).

### Backend APIs and operational requirements

APIs: `POST /search`, `POST /blueprints`, `POST /sources/scan`, `POST /publishers/intake`, `POST /embeddings/jobs`, `POST /evals/runs`, `POST /assets/generate`, `POST /assets/screen`, `GET /primitives/{id}`, `GET /primitives/{id}/deployments`. Operational contract: every index record is reproducible from a source record or curated component; every generated blueprint carries pricing-snapshot ids and assumptions; every verified-source item carries publisher, signature/review method, effective date, source URL, and content hash; every media output carries prompt, model, seed (when available), safety checks, and license/provenance; every primitive can be deprecated, superseded, forked, rated, and benchmarked. For worker-level details see [Object factory worker fleet](object-factory-worker-fleet.md).
