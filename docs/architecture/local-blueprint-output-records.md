# Local Blueprint Output Records

The local sentence-to-pipeline demo should generate more than a temporary UI
response. Each run should be able to emit durable, normalized records that can
be stored in Postgres, embedded, searched, deduplicated, reviewed, and reused
as primitives.

This turns product usage into a controlled object factory. A user sentence can
produce a route matrix, and the route matrix can produce reusable objects:

- model-route records;
- prompt-prefix cache profiles;
- pricing snapshot stubs;
- deployment line items;
- eval arms;
- verified-fact dependency records;
- review-ticket routing rules.

## Record Flow

The local baseline should run without API keys:

1. parse the sentence into task, modalities, risk tier, budget, and hosting;
2. build cheap, balanced, quality-first, and local-first route options;
3. emit normalized records for each option and dependency;
4. link entities such as jurisdictions, agencies, models, tools, and domains;
5. cluster near-duplicate route records;
6. emit keyword, vector, graph, facet, freshness, and cost index records;
7. route high-risk records to review.

This mirrors the million-object ingestion gates while staying useful as a
downloadable demo.

## Privacy and Trust Boundaries

The demo must not write private user content into public catalog objects by
default. It should emit synthetic examples or tenant-private records unless the
user explicitly publishes a curated component. For high-risk domains, the route
record should contain the task class, guardrails, dependencies, and review
policy, not sensitive user evidence.

Verified publisher facts remain separate from model-route records. Route
records reference signed fact dependencies by id and effective date so that a
government or standards-body update can trigger impact analysis and review
tickets without rewriting every pipeline manifest.

## Storage Target

The first implementation can write JSON to stdout or JSONL files. Production
storage should use the canonical Postgres object tables and pgvector indexes,
with object storage for raw snapshots and generated bundles. BigQuery or
ClickHouse can later aggregate pricing traces, cache hit rates, route ratings,
and A/B test outcomes.
