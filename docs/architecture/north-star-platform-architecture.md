# North Star Platform Architecture

Open Harness Hub should scale as a database-backed component registry and factory, not as a pile of files.

The north star is a system where public and verified source surfaces become governed source records, normalized knowledge objects, entity links, labels, dimensions, embeddings, review tickets, and deployable pipeline blueprints. Static docs and repository files are useful bootstrap and export surfaces, but the production product should be backed by canonical database storage, replayable object batches, and auditable workers.

## Product Language

Use **components**, **subcomponents**, **pipelines**, **knowledge packs**, **tools**, **rubrics**, **blueprints**, and **objects** in product and strategy docs.

Avoid implementation-heavy labels for the thing users are building with. A component is an actively used unit that can be searched, rated, versioned, wired into a pipeline, tested, deployed, and updated. A subcomponent is a smaller reusable unit inside a component, such as a check, rule, prompt fragment, fact, schema field, review question, cost dimension, tool call, or evaluation criterion.

Repository files may still exist as import/export definitions while the system is being bootstrapped. They are not the product's canonical long-term storage model.

## Product Shape

A user should be able to describe a task such as:

> Build a low-cost LLM pipeline that intakes a photo and a description, screens for human exploitation risk, cites trusted sources, and routes high-risk cases for review.

The platform should return:

- candidate pipeline blueprints;
- relevant tools, harnesses, rule packs, knowledge packs, and rubrics;
- model and hosting cost estimates;
- deployment options for the user's environment;
- evaluation and regression tests;
- provenance, licensing, trust, and privacy boundaries;
- update paths when verified facts or source rules change.

## Architectural Commitments

The durable architecture is:

1. Postgres as the canonical operational store for components, subcomponents, versions, jobs, source records, labels, dimensions, reviews, ratings, and deployment metadata.
2. Static docs and repository files as generated views, seed definitions, review diffs, and export bundles, not the primary product database.
3. Pgvector as the first semantic search layer, combined with Postgres full-text search, labels, facets, entity links, and graph edges.
4. Object storage for raw snapshots, generated JSONL shards, replayable batches, media assets, and audit components.
5. Redis or a managed queue for source scans, object factory jobs, embedding jobs, pricing refreshes, eval jobs, and review routing.
6. Provider-neutral worker containers for crawling, page conversion, sensitive-data screening, LLM polishing, entity linking, dedupe, embedding, eval, and deployment bundle generation.
7. BigQuery or ClickHouse only after product telemetry, ranking analytics, billing analysis, and cold vector experiments need warehouse scale.

This keeps the early system cheap and understandable while leaving room for high-volume object generation.

## Object Factory Spine

Every high-volume source path should follow the same spine:

```text
source surface
-> source governance routing
-> scan partition and replay record
-> normalized object extraction
-> entity recognition and canonical linking
-> fuzzy dedupe clustering
-> label and dimension assignment
-> keyword/vector/graph/facet index record emission
-> review ticket routing
-> promotion decision
-> canonical Postgres load
-> search readiness audit
```

New tools and pipelines should strengthen this spine. Avoid one-off generators that create objects without provenance, stable IDs, replay records, dedupe hooks, or review routes.

## Search And Retrieval

Search should stay hybrid:

- exact keyword and identifier search for recall and auditability;
- hierarchical labels and schema.org-style labels for explainable filtering;
- custom tenant labels and model-generated dimensions for flexible routing;
- entity links and graph edges for dependency and source traversal;
- embeddings for semantic recall;
- reranking or polishing models only after cheaper filters narrow the result set.

The vector layer is important, but it must not become the only retrieval system. Vector readiness audits should prove that planned embeddings are actually stored and searchable.

## Cost Discipline

The platform should optimize for useful objects per dollar:

- deterministic extraction, hashing, labels, and dedupe before LLM calls;
- local or cheap models for low-risk labeling, reranking, and embedding;
- external high-capability models only for high-value or ambiguous work;
- batch embeddings and model calls;
- pricing snapshots attached to generated blueprints;
- replayable JSONL batches before database mutation;
- audits that distinguish planned work from completed, searchable, committed work.

## What To Build Next

Prefer work that makes the spine more complete:

- source-surface scanners that generate governed source records;
- normalization workers that emit canonical object rows;
- entity/dedupe/index emitters that can run in batches;
- embedding execution and readiness audits;
- Postgres/pgvector load plans and committed-count audits;
- ranking, evaluation, pricing, and deployment blueprints that can be generated from stored objects.

Do not optimize for raw file count. The million-object goal is achieved by a repeatable, governed object factory that can safely generate, store, search, evaluate, and update database-backed components and subcomponents at scale.
