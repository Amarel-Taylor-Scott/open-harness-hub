# 100M Component Infrastructure

The Postgres extension name we should standardize on is **pgvector**. The hosted product can start with Postgres plus pgvector, then split colder analytics into BigQuery or object storage when query cost or storage pressure makes that worthwhile.

## Target Shape

At 100,000,000 components, the database cannot behave like a flat catalog. It needs typed hot paths:

- `component` and `component_version` for reviewed active components.
- `component_candidate` and `subcomponent_candidate` for generated, imported, and review-gated rows.
- `component_pipeline_template` and `component_pipeline_template_step` for off-the-shelf pipelines that string components together.
- `subcomponent` for facts, rules, labels, dimensions, review routes, deployment steps, source spans, and embedding work items.
- `object_embedding` for pgvector-backed retrieval over components, subcomponents, source records, pipeline templates, and traces.
- Object storage for raw captured pages, markdown conversions, media, bulky traces, and replay bundles.

## Scale Rules

1. Keep Postgres as the operational source for reviewed components, candidates, labels, provenance, versioning, and template composition.
2. Use pgvector for hot semantic search and reranking inputs. Partition vector tables by subject type, tenant, embedding model, and time bucket before row counts become painful.
3. Store raw source material outside Postgres. Database rows keep content hashes, storage refs, licenses, trust tiers, and privacy boundaries.
4. Load new rows additively with `COPY`, staging tables, idempotent upserts, and replay summaries. Do not rebuild the world for every batch.
5. Use workers for extraction, enrichment, embedding, dedupe, comparison, verification, promotion, and template generation. Each worker claims shards and writes resumable progress.
6. Treat active components as reviewed products; generated candidates are supply.

## Postgres And pgvector Layout

The first production deployment can run on managed Postgres:

- Primary database: active components, candidates, templates, labels, provenance, subscriptions, billing, and worker state.
- Read replica: search API, browsing UI, and template expansion.
- pgvector indexes: HNSW for hot active components and current templates; IVFFlat or batched exact scans for colder candidate partitions.
- JSONB GIN indexes: flexible metadata, label sets, schema.org mappings, generated dimensions, and tenant-specific labels.
- Partial indexes: review queues, high-risk facts, volatile facts, promoted components, and active templates.
- Daily partitions: high-volume candidate rows, embeddings, traces, comparison pairs, and worker outputs.

BigQuery is useful later for broad analytics, source-surface reporting, historical cost analysis, and offline model-evaluation summaries. It should not be the first operational store for the interactive product because template expansion, review queues, and component promotion need transactional behavior.

## Component Layers

Every reusable component can declare a layer:

- `pre_llm`: input normalization, PII gates, source routing, retrieval, label expansion, prompt budgeting, cost routing.
- `llm`: model adapters, local/browser models, hosted model calls, classifiers, multimodal inference, embedding models.
- `post_llm`: verification, citation, deterministic checks, redaction, review routing, persistence, trace writing.
- `control_flow`: loop, iterate, branch, retry, parallel, fallback, human review, cache lookup, stop.
- `data`: loads, exports, dedupe, entity resolution, vector indexing, shard management.
- `evaluation`: benchmarks, A/B tests, cost-quality comparisons, regression checks.
- `deployment`: Terraform, runtime packaging, container images, MCP setup, cloud function wiring.
- `governance`: publisher verification, licensing, privacy boundaries, facts signed by vetted sources.

This keeps pipeline assembly explainable. A user can ask for a cheap pipeline, and the system can choose cheaper `pre_llm` retrieval, a small `llm` route, stricter `post_llm` verification, and a bounded `control_flow.iterate` loop.

## Off-The-Shelf Pipelines

Off-the-shelf pipelines should be stored as database rows, not only files:

- `component_pipeline_template` stores the reusable task family, cost profile, modalities, industries, and route policy.
- `component_pipeline_template_step` stores ordered steps with component layer, optional control-flow kind, inputs, outputs, and references to active components or candidates.
- Search embeds both the whole template and each step, so “photo plus description exploitation triage” can retrieve a complete pipeline and its modular pieces.
- Cost estimates join template steps to model pricing, runtime pricing, cache-hit assumptions, and expected token/media volume.

The template expander added in this pass is intentionally side-effect free. It proposes a component sequence and writes JSON when asked; promotion into the database remains a separate reviewed load.

## Worker Fleet

For 100M components, worker groups should be containerized and independently scalable:

- Search/spider workers: discover sources, capture pages, and emit source records.
- Conversion workers: page to markdown, OCR, media metadata, transcript extraction.
- Normalization workers: turn source records into component candidates and subcomponent candidates.
- Enrichment workers: labels, schema.org mappings, generated dimensions, entities, jurisdictions, industries, modalities.
- Embedding workers: create pgvector rows by subject type and embedding model.
- Comparison workers: block, compare, dedupe, and resume pairwise jobs without reprocessing completed leaves.
- Verification workers: grounded search, multi-model checks, expert email campaigns, signed source verification.
- Promotion workers: move reviewed candidates into active component tables and version history.

Each worker must be additive and resumable: claim a shard, emit rows, write progress, and make the next run pick up where the last one stopped.
