# Containerized Object Factory Orchestration

The million-object registry needs parallel workers, not one local generation
loop. Workers should be containerized when they need browser automation, custom
system dependencies, source-specific clients, repository checkouts, OCR, media
processing, or tenant-isolated execution.

## Worker Lanes

Use separate queue lanes:

- discovery: find source surfaces, feeds, repos, papers, datasets, workflow
  galleries, public forms, and standards pages;
- spider: crawl approved domains, paginate, archive, hash, and emit source
  records;
- snapshot: save raw HTML, PDF, media, repository metadata, and workflow files
  to object storage;
- normalize: convert pages, PDFs, notebooks, workflow JSON, and READMEs into
  Markdown or structured records;
- enrich: extract candidate primitives, entities, labels, dimensions, and
  dedupe signals;
- embed: batch embeddings for hot pgvector slices and cold warehouse exports;
- verify: run schema, citation, policy, test, eval, and safety checks;
- promote: emit review tickets, promotion decisions, index records, and catalog
  manifest candidates;
- warehouse: export cold shards to BigQuery or another analytic tier.

## Parallelism Contract

Each worker leases a shard, emits append-only outputs, and never directly
publishes public objects. Publication happens through review and promotion
pipelines.

Every shard should carry:

- `partition_id`, `run_id`, `source_surface_id`, and `tenant_id`;
- source governance decision;
- object-storage input/output pointers;
- worker image digest and git commit;
- prompt template id and prompt hash if a model is used;
- model route, pricing snapshot, and estimated cost;
- retry count, error class, and review ticket ids;
- output row counts for `source_record`, `normalized_object`, entities,
  labels, dimensions, embeddings, review tickets, and index records.

## Prompt Cache Savings

Prompt-prefix caching becomes much more likely when harnesses standardize:

- system prompt preambles;
- task instructions;
- JSON schemas;
- tool signatures;
- few-shot examples;
- rubric language;
- output field order;
- refusal and review-ticket language.

The variable user/source content should be isolated late in the prompt. The
stable harness preamble and schema block should appear first and be versioned by
`prompt_template_id`, `prompt_version`, and `prompt_hash`.

This helps two layers:

- provider prefix caches can reuse repeated stable prompt prefixes;
- OpenHubForAI can reuse trajectory fragments, tool-call patterns, and
  verified output skeletons from its own object database.

## Cheap Default Shape

Start with:

- one API service;
- one Redis or managed queue;
- one Postgres/pgvector database;
- one object storage bucket;
- three worker containers: discovery/spider, normalize/enrich, verify/promote.

Split later into specialized containers for browser scraping, repo mining,
workflow mining, embedding batches, BigQuery export, and model-heavy polishing.

## Safety Rules

- Discovery workers may find candidate sources, but source governance decides
  whether they can be scraped, stored, indexed, or published.
- Spider workers must honor allowlists, robots/policy where applicable, rate
  limits, and license boundaries.
- Raw source snapshots stay in object storage and are not republished by
  default.
- Tenant-private outputs never enter shared indexes without explicit promotion.
- Expensive model calls happen after source filtering, dedupe, and sensitive
  data screening.
