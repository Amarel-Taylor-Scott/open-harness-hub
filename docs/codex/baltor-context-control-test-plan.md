# Baltor Context-Control Test Plan

Updated: 2026-06-01

This is the test checklist for the admin demo and local worker stack.

## Local Services

Expected services:

- Admin server on a local port, usually `9304`.
- Redis and Postgres from `infra/docker-compose.context.yml`.
- Context worker container from `infra/docker-compose.context.yml`.
- Ollama exposing an OpenAI-compatible route with `batiai/gemma4-e2b:q4`.
- Optional TryCloudflare tunnel pointing at the active admin server port.

## Smoke Tests

Run after changes to admin demo, workers, routes, exports, or model policy:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py
python3 -m py_compile scripts/context_workers/runner.py
python3 -m py_compile scripts/context_workers/workers/llm_trust_layer.py
python3 -m py_compile scripts/context_workers/workers/node_research.py
python3 -m scripts.context_workers.runner --validate-manifest
```

If the Docker stack is running:

```bash
docker compose -f infra/docker-compose.context.yml ps
docker compose -f infra/docker-compose.context.yml logs --tail=120 context-worker
```

## HTTP Route Checks

Every route should return a nonblank page containing its expected title:

```text
/admin-demo/
/admin-demo/sources
/admin-demo/monitoring
/admin-demo/outputs
/admin-demo/download
/admin-demo/explore
/admin-demo/testing
/admin-dashboard/monitor
/api/health
/api/admin-dashboard/events
/api/admin-dashboard/queue-health
/api/context-gateway/status
/api/context-gateway/connectors
/api/context-gateway/sync-contracts
/api/debug/heartbeat
```

The six-card home must link to:

```text
Load data -> /admin-demo/sources
Processing -> /admin-demo/monitoring
Outputs -> /admin-demo/outputs
Download -> /admin-demo/download
Explore context -> /admin-demo/explore
Integration testing -> /admin-demo/testing
```

## Upload Proof

The strongest local proof is a synthetic ZIP with nested folders:

```text
company/acme-profile.txt
company/leadership/current-officers.md
company/ownership/employment-agency-network.md
policies/access-control.md
policies/archived/old-access-control.md
web/domain-record.txt
```

The test should upload the ZIP, follow the redirect, poll the run API, and
assert:

- run exists;
- `document_tree.summary.files > 1`;
- `document_tree.summary.folders > 1`;
- pages and components were created;
- the corpus includes temporal ownership-chain facts such as acquisition,
  merger, split/spinout, and conflicting current-ownership records;
- the corpus includes documentation terminology risks such as a multi-meaning
  business term, an undefined domain term, and an acronym without a
  source-local definition;
- ownership-chain facts become first-class `ownership_change` claim records
  with event types, detected source dates, temporal fragility, refresh flags,
  and safe-context instructions;
- parent-company and independent-ownership records for the same company become
  `ownership_conflict_groups` so context packs warn before stating current
  ownership;
- dated ownership conflict groups identify the newest dated claim, older
  candidate-superseded claims, a deterministic `resolution_suggestion`, and a
  bounded `supersession_confidence` without promoting the newer claim to a
  verified current fact;
- term-clarity risks become first-class `term_clarity_concerns` with
  `MULTI_MEANING_TERM`, `UNDEFINED_DOMAIN_TERM`, or
  `ACRONYM_WITHOUT_DEFINITION` type, evidence, claim IDs, glossary-review
  requirement, and safe-context instructions;
- term-clarity risks also produce source-scoped
  `glossary_resolution_packets` with review routes, proposed glossary entries,
  and safe-context policy that blocks global memory and canonical graph
  promotion until review;
- time-sensitive ownership records produce `ownership_refresh_jobs` with
  `context.search.verify` task shape, queue policy, budget policy, and adapter
  plans that keep person-level OSINT disabled while allowing configured
  non-PII public business sources;
- Redis queue handoff event exists;
- worker ledger record exists for the run;
- queue drains to zero;
- missing/not-configured adapter counts are zero in local mode;
- local LLM status is either `executed` or explicitly reports model
  unavailability;
- all exports return valid JSON.
- context gateway search returns a typed context pack with `ctx://` source
  handles.
- context gateway fetch expands one returned handle under a bounded token
  policy.
- local cache writer can save the typed context pack and glossary packets to a
  temporary Markdown cache, retain `ctx://baltor/...` source handles, write a
  `baltor.local-context-cache-manifest` manifest plus JSONL audit event,
  and preserve the no-raw-source-dumps policy.
- context sync contracts expose push, pull, and push-then-pull modes; trigger
  types for commits, pushes, MR updates, artifacts, watchers, and schedules;
  check gates; artifact manifest kinds; and worker routing.
- connector catalog exposes governed connector envelopes and does not expose
  unrestricted raw source tools by default.
- debug heartbeat reports server, run, queue, worker, event, and contract
  state.

When running with `--isolated-worker --wait-worker-seconds`, the proof should
queue the ZIP run before connector-envelope runs. This keeps the worker wait
focused on the nested ZIP pipeline instead of waiting behind connector
follow-up jobs.

## Browser Checks

Use Playwright if installed. If not installed, use Chromium screenshot or HTTP
checks rather than stopping.

Suggested browser assertions:

- Home page has six cards.
- Clicking each card changes the URL to the dedicated route.
- `/admin-demo/sources` has file upload, raw text fallback, and gateway
  connector envelope input.
- `/admin-dashboard/monitor` auto-refreshes and shows events.
- `/admin-dashboard/monitor` shows a Queue health section with active worker
  jobs, backlog trend, pending delta, sample count, and a pending backlog
  sample, plus worker throughput and drain ETA when recent completion events
  are available. It should also show whether persisted queue-health history has
  been loaded.
- `/api/admin-dashboard/queue-health` returns `baltor.queue-health` with
  active jobs, pending sample, recent worker events, thresholds, warnings,
  `trend`, `throughput`, `history`, and `recent_samples`.
- queue throughput includes `throughput.by_family`, `pending_family_counts`,
  and `pending_family_scan` so deterministic, node-research, context-gateway,
  and local-LLM work are distinguishable.
- No route is a blank page.
- Text does not overflow obvious buttons or cards at desktop width.

## Worker Ledger Checks

Inspect recent worker records for a run:

```text
context.pipeline.pass
context.pipeline.experimental_adapters
context.ambiguity.scan
context.conflict.scan
context.fragile_fact.enrich
node.research.plan
node.research.enrich
llm.trust.plan
llm.claim.review
llm.graph.enrich
llm.context.summarize
llm.audit.review when high risk
```

The demo should surface these records on the monitor or run API. A user should
not have to open the ledger file to know what happened.

## Export Contracts

Expected exports:

- `manifest`: run metadata, sources, hierarchy summary, package links, worker
  status, and compatibility notes.
- `text`: extracted text claims/chunks/components with source metadata.
- `rag`: JSON/JSONL-like records with text, chunk/page references, source
  hierarchy, freshness flags, and citation fields.
- `graph`: nodes, edges, claims, proposed LLM graph additions, controlled edge
  types, evidence IDs, and `OwnershipChangeEvent` nodes connected by
  `PROPOSES_OWNERSHIP_EVENT` edges with promotion disabled.
  Dated current-status disagreements should create `OwnershipConflictGroup`
  nodes connected by `HAS_OWNERSHIP_CONFLICT` edges. When a newer dated
  ownership record likely supersedes an older dated current-status record, the
  graph should add a `MAY_SUPERSEDE_OWNERSHIP_CLAIM` edge from the newer claim
  to the older claim with confidence and `promotion_allowed: false`. Term
  ambiguity should create `TermClarityConcern` nodes and
  `HAS_TERM_CLARITY_CONCERN` edges with promotion disabled. Glossary review
  packets should create `GlossaryResolutionPacket` nodes and
  `HAS_GLOSSARY_RESOLUTION_PACKET` edges with promotion disabled.
- `audit`: worker records, trust concerns, fragile facts, conflicts,
  ambiguity, LLM reviews, safe-context policy, and model routes.
- `safe-context`: approved/candidate context with source handles, warnings,
  fragile facts, summaries, use instructions, ownership refresh caveats, and
  planned refresh jobs.
- `context-pack`: coding-agent context pack with summary, facts, code pointers,
  risks, next fetches, source handles, token budget metadata, and gateway
  policy. Ownership facts should include event type, temporal fragility,
  refresh requirement, entity candidates, conflict groups, and source-date-safe
  instructions. Ownership conflict groups should include
  `resolution_suggestion`, `latest_claim_id`, `superseded_claim_ids`, and
  `supersession_confidence`. It should also expose `ownership_refresh_jobs` so
  a coding agent can see how current ownership claims would be refreshed
  without calling unrestricted raw tools. It should expose
  `term_clarity_concerns` and include term-specific risks so poorly defined or
  multi-meaning terms are not flattened into stable context.
- `context-objects`: standardized context object graph projection with
  `baltor.context-object`, `baltor.context-version`,
  `baltor.context-artifact`, `baltor.context-relationship`,
  `baltor.context-assertion`,
  `baltor.context-dimension-definition`,
  `baltor.context-dimension-value`, `baltor.context-event`, and
  `baltor.context-pack` records. It should prove immutable versions,
  derived artifacts with lineage, typed relationships, source-linked
  assertions, flexible facets, 5W1H projections, first-class dimensions,
  append-only events, and one pack projection.
- `context-dimensions`: bounded gateway view of
  `baltor.context-dimension-definition` and
  `baltor.context-dimension-value` records, filterable by run, dimension, or
  subject without requiring clients to download the full `context-objects`
  export.
- UI dimension panel: after a run, `/admin-demo/explore` and
  `/admin-dashboard/monitor` should show `Dimension engine`, `Highest
  operational risk`, and `Lowest verifiability` sections.
- Postgres persistence: `db/postgres/schema.sql` should include the
  `context_object`, `context_version`, `context_relationship`,
  `context_assertion`, `context_dimension_definition`,
  `context_dimension_value`, `context_artifact`, `context_lineage_event`, and
  `context_pack` tables. In environments with `psql`, run the schema against a
  disposable database to validate DDL compatibility.
- Model routing: `/api/context-gateway/model-routing` should return
  `baltor.context-model-routing`, at least seven provider-neutral model
  profiles, a routing policy with `provider_neutral: true`, and a sample route
  decision. MCP self-test should include `context_model_routing`.
- `glossary`: source-scoped glossary resolution packets, term concerns, and
  policy blocking global memory/canonical graph promotion until a term is
  reviewed.

## Context Gateway Contract

Expected local HTTP proof endpoints:

```text
/api/context-gateway/status
/api/context-gateway/connectors
/api/context-gateway/search
/api/context-gateway/fetch
/api/context-gateway/trace
/api/context-gateway/glossary
/api/context-gateway/context-object-schema
/api/context-gateway/context-schema-catalog
/api/context-gateway/product-surface
/api/debug/heartbeat
```

Assertions:

- status says Baltor owns retrieval policy and ACL filtering before model
  exposure;
- search returns `context_pack.source_handles`;
- search returns `retrieval.acl_filter_applied: true`;
- fetch accepts a returned `ctx://baltor/...` handle and returns one bounded
  component or claim;
- trace says raw source access is fallback, not default retrieval.
- glossary returns `baltor.context-glossary` packets, can filter by `term`,
  and blocks global memory and canonical graph promotion by default.
- context object schema returns `baltor.context-object-schema`, the durable
  `baltor.context-object` kind, the `ctx://` source-handle pattern, and the
  standards profile used for MCP delivery, JSON Schema validation,
  JSON-LD/schema.org semantics, PROV provenance, Web Annotation evidence
  selectors, RO-Crate packaging, SPDX/CycloneDX artifacts, OpenLineage
  lineage, and OpenTelemetry traces.
- context schema catalog returns `baltor.context-schema-catalog` and exposes
  schema kinds for objects, immutable versions, derived artifacts, typed
  relationships, append-only events, and task-specific context packs.
- product surface returns `baltor.context-product-surface` and exposes
  Context Fabric modules, interfaces, deployment models, standards mappings,
  MVP phases, and product invariants.
- model routing returns `baltor.context-model-routing`, at least seven
  provider-neutral model profiles, and a risk-based sample route decision.
- reranking returns `baltor.context-reranking`, at least seven source-aware
  reranker profiles, and a policy that treats LoRA/domain rerankers as
  eval-gated adapters with lineage rather than global truth.
- connectors returns Jira, Confluence, GitLab, website, FTP/SFTP, drive, and
  object-store style connector envelopes with ACL-before-model policy.
- heartbeat returns `kind: baltor.debug_heartbeat`, server uptime, run
  heartbeat, latest per-run worker event, recent per-run worker events, queue
  stats, oldest pending job age, pending job sample, latest worker event ID,
  pending-sample missing timestamp count, recent worker stream events, and
  active worker jobs inferred from claimed/closed stream events, stale
  active/pending warning counts, queue thresholds, and recent worker heartbeat
  metadata.

MCP wrapper proof:

```bash
python3 scripts/baltor_context_gateway_mcp.py \
  --base-url http://127.0.0.1:9304 \
  --self-test
```

Assertions:

- wrapper exposes `context_status`, `context_search`, `context_fetch`,
  `context_trace`, `context_connectors`, `context_sync_contracts`,
  `context_object_schema`, `context_schema_catalog`,
  `context_product_surface`, `context_heartbeat`, `context_queue_health`, and
  `context_glossary`;
- self-test reaches the local gateway;
- search returns at least one source handle;
- fetch expands one returned handle;
- trace returns policy steps.
- connectors returns governed connector definitions.
- heartbeat returns the debug heartbeat contract.
- queue health returns the `baltor.queue-health` contract.
- glossary returns the `baltor.context-glossary` contract.
- context object schema returns `context_object_kind:
  baltor.context-object`.
- context schema catalog returns `baltor.context-schema-catalog` and at
  least sixteen schema kinds.
- product surface returns `baltor.context-product-surface`.
- model routing returns `baltor.context-model-routing`.
- reranking returns `baltor.context-reranking`.

## Closeout Proof

A closeout should state:

- local URL;
- TryCloudflare URL if running;
- run ID tested;
- files uploaded or sample used;
- routes tested;
- export kinds tested;
- context gateway search/fetch status;
- queue state;
- worker status;
- any unavailable optional dependency.
