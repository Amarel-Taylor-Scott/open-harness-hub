# Local Blueprint Record Persistence

The local sentence-to-pipeline demo now emits normalized output records. The
next step is to convert those records into the canonical row families used by
the Postgres and pgvector bootstrap path.

The persistence layer should treat every demo run as a governed source:

1. create a tenant-private `source_record` with prompt hash and no raw prompt by
   default;
2. convert route, prompt-cache, pricing, eval, and fact-dependency records into
   `normalized_object` rows;
3. emit simple `canonical_entity` rows for task type, risk tier, modalities,
   route names, and review queues;
4. connect records to entities through `object_entity_ref`;
5. create deterministic `dedupe_cluster` rows by object type and content hash;
6. emit `review_ticket` rows for high-risk, regulated, public-safety, volatile,
   or live-pricing-required records;
7. emit `index_record` rows for keyword, facet, graph, freshness, quality, and
   cost search.

This keeps the local demo compatible with the same ingestion path used for
large factories. The first implementation can write JSONL shards locally. The
same shards can later be bulk-loaded into Postgres, indexed with pgvector, and
mirrored into BigQuery or ClickHouse for cost and usage analytics.

## Privacy

By default, the source record stores only:

- prompt hash;
- task parse;
- route metadata;
- run mode;
- privacy boundary;
- generated object ids.

Raw prompts and uploaded evidence stay tenant-private unless the user
explicitly publishes a curated component. Public catalog seed data should remain
synthetic.

## Search Payoff

Once persisted, future user requests can retrieve prior route records before
calling a model. That enables:

- cheaper blueprint generation;
- reuse of proven guardrail and eval patterns;
- prompt-prefix cache recommendations;
- verified-fact impact analysis;
- route ratings and deployment telemetry;
- model swaps as prices and capabilities change.
