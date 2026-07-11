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

## Demo run as controlled object factory (consolidated)

> Folds the durable design of the merged local-blueprint-output-records plan — how a keyless local demo run emits durable primitives through the same ingestion gates.

The local sentence-to-pipeline demo should emit more than a temporary UI response: each run becomes a controlled object factory. A user sentence produces a route matrix, and the route matrix produces reusable objects — model-route records, prompt-prefix cache profiles, pricing snapshot stubs, deployment line items, eval arms, verified-fact dependency records, and review-ticket routing rules. Record flow (keyless baseline, no API keys required): parse the sentence into task / modalities / risk tier / budget / hosting → build cheap, balanced, quality-first, and local-first route options → emit normalized records for each option and dependency → link entities (jurisdictions, agencies, models, tools, domains) → cluster near-duplicate route records → emit keyword/vector/graph/facet/freshness/cost index records → route high-risk records to review. This mirrors the million-object ingestion gates while staying useful as a downloadable demo. Privacy/trust: the demo never writes private user content into public catalog objects by default (synthetic or tenant-private unless the user explicitly publishes); for high-risk domains the route record carries the task class, guardrails, dependencies, and review policy — not sensitive evidence. Verified publisher facts stay separate from model-route records: routes reference signed fact dependencies by id and effective date so a government or standards-body update can trigger impact analysis and review tickets without rewriting every manifest. Storage target: first implementation writes JSON/JSONL locally; production uses the canonical Postgres object tables and pgvector indexes with object storage for raw snapshots, and BigQuery/ClickHouse can later aggregate pricing traces, cache hit rates, route ratings, and A/B outcomes.
