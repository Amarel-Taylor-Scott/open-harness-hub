# CLAUDE.md - Open Harness Hub Agent Instructions

This file is for Claude Code, Claude desktop/browser agents, and any Claude 4.x/4.8/4.7-style workflow that opens this repository. Follow `AGENTS.md` first; this file adds speed and organization rules for scaling Open Harness Hub.

## North Star

Build a database-backed registry of reusable AI pipeline components and subcomponents that can scale from thousands to millions of rows without turning every row into a public static file.

The product is not a pile of static definitions. It is a component network:

- pre-LLM components: intake, OCR, normalization, source governance, entity linking, dedupe, routing, cost gates;
- LLM/model components: local models, hosted model routes, browser models, embedding models, rerankers, fine-tuning/training jobs, multimodal generators;
- post-LLM components: verification, scoring, review queues, CDC propagation, signed publisher updates, deployment blueprints;
- runtimes: local Python, Docker, Render workers, Cloud Run, Kubernetes, MCP servers, pgvector, BigQuery/ClickHouse telemetry, object storage.

Use "components" and "subcomponents" in new prose and user-facing docs. Avoid introducing new uses of "artifact", "manifest", or "primitive" unless you are quoting an existing schema, filename, or legacy phrase.

## Default Fast Path

Do not start with full catalog rebuilds. The normal loop is:

```bash
python3 scripts/validate.py <changed catalog paths>
python3 scripts/build_component_id_index.py --update <changed catalog paths>
python3 scripts/build_catalog_pages.py --paths <changed catalog paths> --update-index
python3 scripts/validate.py --global-ref-check <changed pipeline paths>
python3 scripts/build_component_id_index.py --check-fresh
```

Use full release gates only when explicitly requested or when changing schemas, vocabularies, or broad catalog references:

```bash
python3 scripts/validate.py
python3 scripts/build_catalog_pages.py
```

If a full rebuild takes too long, do not keep repeating it. Capture the bottleneck and improve the incremental path.

## Daily Factory Target

Every serious development turn should improve at least one of these:

- generate 1,000 to 5,000 database-backed component candidates per day;
- generate 5 to 25 showcase pipelines per day;
- reduce duplicate collapse during row merges;
- improve source governance, entity linking, fuzzy dedupe, index records, review routing, embedding execution, or promotion readiness;
- make staged rows easier to load into Postgres/pgvector safely;
- make component IDs, hashes, CDC events, and index deltas more deterministic.

High-volume rows belong in JSONL staging and Postgres/pgvector load plans, not thousands of new hand-written static pages.

## Required Row Families

A scalable factory batch should emit or preserve:

- `source_record`
- `normalized_object`
- `canonical_entity`
- `object_entity_ref`
- `dedupe_cluster`
- `label_assignment`
- `dimension_value`
- `object_embedding`
- `index_record`
- `review_ticket` when risk warrants review

Do not report raw generated lines as active components. Separate:

- generated candidate rows;
- unique staged rows;
- candidate-table load readiness;
- active promotion readiness;
- committed Postgres rows;
- vector search product readiness.

## ID And Hash Discipline

Never rely on truncation alone for generated IDs. Long generated component IDs must include stable hash suffixes so daily batches do not collapse during dedupe, index merge, or CSV load planning.

Use canonical hashes for:

- normalized object body;
- component version definition;
- source content;
- index record identity;
- command approval records;
- replay and CDC events.

Formatting changes should not create false versions. Source content changes should be detectable even when the wrapper stays the same.

## No Magic Values (Single Source Of Truth)

Never hand-type a value that has to be remembered and updated in more than
one place. At scale, a value typed twice is a value that drifts.

- Numbers that describe the repo (component counts, totals per type, "N
  emitters", spec/catalog version, build date) are **computed**, never typed
  into prose. The README count drifting from `172` to thousands is the
  canonical bug — do not reintroduce it.
- A value used in more than one place (embedding dimension, model IDs,
  thresholds, canonical paths, row-family/type names) gets **one definition**
  and is imported everywhere else. Put shared constants in a config module;
  put shared lists in `vocabularies/`/`schemas/` and read them.
- A string that embeds a constant's value is built from the constant
  (`f"vector({DEFAULT_SCHEMA_DIMENSIONS})"`), never a parallel literal
  (`"vector(384)"`).
- Every meaningful literal in logic is a named constant with a unit/rationale
  comment. Where a value must be mirrored, add a validate/CI check that fails
  on drift.

Full rules, examples, and remediation: `docs/codex/no-magic-values.md`.

## Promotion Boundary

Candidate-table load readiness is not active publication readiness.

A candidate can be structurally load-ready when it has source, dedupe, content hash, embedding work, and index records. It must not become tenant-visible while it has:

- open review tickets;
- high-risk review requirements;
- placeholder embeddings;
- unresolved source or signature questions;
- volatile public facts without CDC/revocation handling.

Use `scripts.db.daily_promotion_readiness_plan` after large row generation.

## Safety And Scope

Do not store real PII, secrets, confidential data, or proprietary dumps. Use synthetic or public metadata only. Do not republish `_reference/`.

Stay away from insurance-related pipelines in new work. If legacy insurance examples already exist, do not expand them.

For sensitive domains, prefer review queues, verified facts, signed publishers, redaction, provenance, and deterministic gates over "just ask the model."

## What To Do When Stuck

If one source path is blocked, switch paths:

- generate showcase pipelines;
- add promotion/readiness tooling;
- improve load audits;
- add source-surface seeds;
- add repair planners for missing row families;
- add documentation that prevents repeated slow or incorrect paths.

Do not stop because one scraper, API, provider, or full rebuild is slow.
