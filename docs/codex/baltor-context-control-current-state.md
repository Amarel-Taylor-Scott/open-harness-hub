# Baltor Context-Control Current State

Updated: 2026-06-01

This is the fast orientation file for long-running Baltor admin-demo and
context-worker iteration. It records the current working assumptions, active
URLs, configured local services, and the pieces that must remain wired together.

## Active Local Demo

- Local admin demo: `http://127.0.0.1:9304/admin-demo/`
- Local monitor: `http://127.0.0.1:9304/admin-dashboard/monitor`
- Current TryCloudflare demo: `https://pepper-rolled-obligations-council.trycloudflare.com/admin-demo/`
- Current TryCloudflare monitor: `https://pepper-rolled-obligations-council.trycloudflare.com/admin-dashboard/monitor`
- Current TryCloudflare gateway status:
  `https://pepper-rolled-obligations-council.trycloudflare.com/api/context-gateway/status`

If the server is restarted on a new port, update this file and the goal prompt
before ending the run.

## Working Stack

- Admin server: `scripts/baltor_admin_demo_server.py`
- Worker runner: `scripts/context_workers/runner.py`
- Worker manifest and tasks: `scripts/context_workers/tasks.py`
- LLM trust workers: `scripts/context_workers/workers/llm_trust_layer.py`
- Node research workers: `scripts/context_workers/workers/node_research.py`
- Tool adapter policy: `scripts/context_workers/workers/tool_adapters.py`
- Docker Compose: `infra/docker-compose.context.yml`
- Worker artifacts: `dist/context-worker-artifacts/`
- Worker ledger: `dist/context-workers-ledger.jsonl`
- Local model endpoint: `http://127.0.0.1:11434/v1`
- Docker model endpoint: `http://ollama:11434/v1`
- Current local CPU model: `batiai/gemma4-e2b:q4`

## Current Capabilities

The demo should support:

- Six-card admin home.
- Dedicated pages for Load Data, Processing, Outputs, Download, Explore
  Context, and Integration Testing.
- File upload, raw text fallback, connector simulation, and governed connector
  envelope registration for Jira, Confluence, GitLab, website, FTP/SFTP, drive,
  and object-store style mirrors.
- ZIP upload extraction with folder hierarchy, files, pages, and text
  components.
- Redis queue handoff from front-end run creation to container workers.
- Background worker processing with deterministic extraction, ambiguity scan,
  conflict scan, fragile-fact records, node research, LLM claim review, LLM
  graph enrichment, LLM summaries, and audit review.
- Local adapter mode by default. External OSINT/API adapters must be explicitly
  enabled.
- Local LLM jobs should auto-approve when they are local, read-only, and within
  configured budget policy.
- Monitor page should expose uploads, queue actions, worker records, ledger
  events, exports, and API activity.
- Export APIs should produce manifest, text, RAG, graph, audit, safe-context,
  context-pack, and glossary packages.
- Local context gateway HTTP APIs should expose bounded search/fetch/status
  contracts with `ctx://baltor/...` source handles:
  `/api/context-gateway/status`, `/api/context-gateway/search`,
  `/api/context-gateway/fetch`, `/api/context-gateway/trace`,
  `/api/context-gateway/connectors`, `/api/context-gateway/sync-contracts`,
  `/api/context-gateway/glossary`, `/api/debug/heartbeat`, and
  `/api/admin-dashboard/queue-health`.
- Local MCP-style wrapper:
  `python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304`.
  It exposes `context_status`, `context_search`, `context_fetch`,
  `context_trace`, `context_connectors`, `context_sync_contracts`,
  `context_heartbeat`, `context_queue_health`, and `context_glossary` over
  stdio JSON-RPC with Content-Length framing.
- Admin operational-readiness API:
  `/api/admin-dashboard/operational-readiness`. It exposes database-backed
  visibility for catalog manifest import status, object governance status,
  archive-candidate review contracts, and setting drift/registry status. The
  local demo reads generated bridge artifacts and canonical schema capabilities;
  hosted deployments should source the same contract from database views and
  setting rows.
- Admin live monitor:
  `/admin-dashboard/monitor` now renders the same operational-readiness summary
  and compact JSON contract alongside queue, heartbeat, dimension-engine, and
  event visibility.
- Local MCP-style wrapper also exposes `context_operational_readiness`, a
  read-only tool that returns the same operational-readiness contract for
  coding agents and integration checks.
- Local Claude Code skill:
  `.claude/skills/baltor-context-gateway/SKILL.md`.
- Local Claude Code command:
  `.claude/commands/baltor-cache-context.md`.
- Local cache status command:
  `.claude/commands/baltor-cache-status.md`.
- Local context cache writer:
  `python3 scripts/baltor_context_cache.py --base-url http://127.0.0.1:9304`.
  It writes compact Markdown context/glossary cache files plus a JSONL audit
  event while keeping raw source-system dumps out of local memory.
- Local context client/SDK shim:
  `scripts/baltor_context_client.py`. It centralizes the HTTP contracts for
  status, search, fetch, trace, connectors, glossary, heartbeat, and queue
  health so cache writers, hooks, commands, and future sync tools do not copy
  request shapes.
- Offline local cache reader:
  `scripts/baltor_context_cache_read.py`. It reads `cache-manifest.json` for
  local Markdown/Obsidian/Basic Memory style sync without contacting the
  gateway.
- Repo-wiki context research:
  `archive/legacy/docs/research/repo-wiki-context-tools.md`. It tracks DeepWiki,
  DeepWiki-Open, OpenDeepWiki, RepoWiki, RepoAgent, CodeWiki, repowise,
  Synthadoc, and local LLM wiki/memory systems as candidate repo-context
  compilers behind the Baltor gateway.
- Connector catalog now includes a governed `repo_wiki` connector envelope for
  DeepWiki/OpenDeepWiki/RepoWiki/RepoAgent-style generated repo context.
  It advertises event-driven sync triggers such as post-commit hooks,
  push/MR webhooks, pipeline artifacts, file watchers, and scheduled polling.
- Event-driven sync architecture:
  `archive/legacy/docs/architecture/baltor-event-driven-context-sync.md`. It defines push,
  pull, and hybrid sync modes; trigger normalization; check gates; artifact
  manifests; and worker routing for commits, pushes, edits, pipelines, and
  generated repo-wiki artifacts.
- Context object standards profile:
  `docs/architecture/baltor-context-object-standards.md` and
  `schemas/context-object.schema.json`. This distinguishes framework runtime
  context schemas, such as LangChain `contextSchema`, from persistent
  source-linked Baltor context objects.
- Local context-kit guide:
  `docs/codex/baltor-claude-code-context-kit.md`.
- Project MCP config: `.mcp.json` registers `baltor-context-gateway` for local
  clients and points it at `http://127.0.0.1:9304`.

## Safety And Policy

- Do not delete local project files to clean up unless explicitly requested.
- Do not treat git tracked/untracked status as permission to delete.
- Do not commit real PII, PHI, secrets, credentials, tokens, private keys, or
  proprietary customer documents.
- OSINT-style enrichment must be authorization-gated for sensitive person-level
  research. Non-PII public business, website, address, registry, and public
  record checks can be enabled through explicit adapter configuration.
- LLMs may review and propose nodes, edges, summaries, ratings, conflicts, and
  warnings. They should not silently promote weak facts into safe context.
- Changing facts belong in the graph, source cache, tools, or knowledge packs,
  not in model weights.

## Known Implementation Direction

The desired pipeline is:

```text
Documents / connectors / ZIPs
-> upload manifest and hierarchy
-> normalized files, pages, blocks, tables, images, and components
-> deterministic parsing and NLP
-> entity, claim, and edge candidates
-> local evidence and configured OSINT enrichment
-> claim-and-trust graph
-> cheap local LLM review
-> larger/open/frontier escalation only when needed
-> safe context packs with citations, caveats, source dates, and audit trails
```

## MCP Context Gateway Direction

Baltor should act as the controlled context gateway for coding agents. Claude
Code and similar tools should call one disciplined MCP interface; Baltor should
own retrieval policy, ACL filtering, hybrid search, reranking, compression,
citations, source handles, audit, and live source fallback. See
`docs/architecture/baltor-mcp-context-gateway.md`.

## Immediate Quality Bar

Before declaring the demo healthy, prove:

- Every six-card route returns nonblank HTML.
- ZIP upload creates a run with hierarchy summary.
- Redis queue receives a job and drains.
- Worker ledger writes records for the run.
- No worker task is stuck in `approval_required` or `budget_blocked` for local
  read-only LLM work.
- Missing/not-configured adapter counts are zero in local mode.
- At least one LLM trust-layer worker reaches `adapter_status: executed` when
  Ollama is available.
- All export links return valid JSON.
- Context gateway search returns a typed context pack with source handles.
- Context gateway fetch expands one handle without dumping unlimited raw source.
- Local cache writer stores bounded context and glossary packets with source
  handles, writes a `baltor.local-context-cache-manifest.v1` manifest, then
  records an auditable local memory write event.
- Context gateway connector catalog returns governed connector envelopes.
- Debug heartbeat returns server, run, queue, worker, event, and contract state.
- Monitor JSON and HTML show the run and recent events.

## Latest Verified Proof

The updated server was verified on `http://127.0.0.1:9304` with
`scripts/test_baltor_admin_demo_flow.py` after adding first-class temporal
ownership-change claim/event typing, ownership refresh planning,
deterministic supersession scoring for dated ownership conflicts, and
deterministic terminology-clarity detection for documentation terms that can
confuse downstream LLMs, plus source-scoped glossary resolution packets.

Proof run:

- run ID: `adm-6a796dfcf1`
- connector-envelope proof run: `adm-2662b7f032`
- upload type: nested ZIP
- extracted hierarchy: 6 folders, 7 files, 7 pages, 22 components
- ownership-change records: 6 event records: `acquisition`, `merger`,
  `split_or_spinout`, `current_parent_record`,
  `independent_ownership_record`, and
  `ownership_conflict_or_refresh_notice`
- ownership refresh caveats: 3 records require refresh before being stated as
  current ownership
- ownership conflict groups: 1 group for `CareShift Partners`, linking the
  2025-11-20 parent-company record and the 2026-02-10 independent-ownership
  record as an apparent temporal conflict
- ownership supersession scoring: the `CareShift Partners` conflict group
  records `latest_claim_id: fact-010`, `superseded_claim_ids: [fact-009]`,
  `resolution_suggestion:
  newer_independent_record_likely_supersedes_parent_record`, and
  `supersession_confidence: 0.68`
- ownership refresh jobs: 4 planned jobs, including 3 current-status refresh
  jobs and 1 conflict-reconciliation job. These use `context.search.verify`,
  carry queue/budget policy metadata, and keep person-level OSINT disabled.
- term clarity concerns: 12 records across `MULTI_MEANING_TERM`,
  `UNDEFINED_DOMAIN_TERM`, and `ACRONYM_WITHOUT_DEFINITION`. The proof corpus
  includes `agency` as a multi-meaning term, `active vendor` as an undefined
  domain term, and `CCO` as an acronym without a source-local definition.
- glossary resolution packets: 12 source-scoped packets. The filtered gateway
  route `/api/context-gateway/glossary?term=agency` returns one
  `baltor.glossary-resolution-packet.v1` packet that blocks global memory and
  canonical graph promotion until glossary review.
- routes checked: `/admin-demo/`, `/admin-demo/sources`,
  `/admin-demo/monitoring`, `/admin-demo/outputs`, `/admin-demo/download`,
  `/admin-demo/explore`, `/admin-demo/testing`, `/admin-dashboard/monitor`,
  `/api/context-gateway/glossary`
- exports checked: manifest, text, RAG, graph, audit, safe-context,
  context-pack, glossary
- gateway checked: context search, source handle fetch, trace policy,
  connector catalog, glossary packet lookup, and heartbeat
- connector catalog checked: 8 governed connectors; raw unrestricted tools are
  not exposed by default; connector manifest includes ACL-before-model policy
- repo-wiki connector checked: catalog includes governed `repo_wiki` adapter
  with raw repo scans as fallback only and generated docs marked as derived
  context. The connector now also declares supported event triggers and requires
  commit-scoped outputs for repo-wiki artifacts.
- queue proof: Redis reachable; approval, budget-blocked, and permanent-failure
- queues were approval/budget/permanent-failure clean; worker event stream was
  live; shared queue had 180 pending local jobs from repeated live proof runs
  and local LLM follow-ups.
- heartbeat queue telemetry now includes pending job samples, missing timestamp
  counts for inherited old jobs, recent worker stream events, and inferred
  active worker jobs.
- Monitor HTML includes a Queue health section that renders active jobs and a
  pending backlog sample without requiring raw JSON inspection.
- `/api/admin-dashboard/queue-health` returns `baltor.queue-health.v1` for
  external monitors.
- Queue health now includes active/pending stale thresholds, stale counts, and
  warnings. Latest proof showed zero stale active jobs, 10 stale pending sample
  jobs, and one stale-pending warning once the inherited backlog crossed the
  configured threshold.
- Queue health now records an in-process rolling sample window with backlog
  trend status, pending delta, active/stale deltas, sample count, and recent
  samples. The monitor renders trend, delta, and sample-count pills so a user
  can distinguish shrinking, flat, and growing backlog behavior.
- Queue health now estimates worker throughput from recent `worker.job.closed`
  stream events. It reports completion count, window seconds, jobs per minute,
  and an estimated drain time when enough completions are available.
- Queue health samples now persist to
  `dist/baltor-queue-health-history.jsonl` and are lazily loaded after admin
  server restarts. Latest proof showed `history.exists: true` and
  `history.loaded_sample_count: 53`.
- Queue throughput is split by task family. The latest proof surfaced
  separate pending counts, completion rates, and drain estimates for
  `context_gateway`, `deterministic_pipeline`, `local_llm_review`, and
  `node_research`.
- The synthetic proof corpus now includes a temporal business-ownership
  scenario for employment agencies being acquired, merged, split into a new
  division, and later reported with conflicting current ownership. This keeps
  the demo pointed at changing business facts that need source dates,
  supersession handling, and refresh warnings.
- Ownership-change claims now carry `claim_type: ownership_change`,
  `detected_dates`, `temporal_fragility`, `requires_refresh`,
  `safe_context_instruction`, entity candidates, and an `ownership_change`
  record. Graph exports create `OwnershipChangeEvent` nodes,
  `OwnershipConflictGroup` nodes, `PROPOSES_OWNERSHIP_EVENT` edges, and
  `HAS_OWNERSHIP_CONFLICT` edges with `promotion_allowed: false`. Dated
  current-status conflicts also create
  `MAY_SUPERSEDE_OWNERSHIP_CLAIM` edges from the newest dated claim to older
  claims, with confidence and promotion disabled.
- Ownership refresh planning now appears in audit and context-pack exports as
  `ownership_refresh_jobs`, with preferred non-PII business sources such as
  official registries, company websites, supplier portal exports, archived
  sources, and second independent sources.
- Context packs now include ownership conflict `resolution_suggestion`,
  `latest_claim_id`, `superseded_claim_ids`, and `supersession_confidence`.
  The gateway risk list includes the suggestion while still requiring refresh
  before stating current ownership.
- Term clarity concerns now appear in manifest, text, graph, audit,
  safe-context, and context-pack exports. Graph exports create
  `TermClarityConcern` nodes and `HAS_TERM_CLARITY_CONCERN` edges with
  promotion disabled. Context packs include glossary-review risks and
  source-scope instructions so ambiguous terms are not converted into stable
  graph nodes or edge labels.
- Glossary resolution packets now appear in graph, audit, safe-context,
  context-pack, and dedicated glossary exports. Graph exports create
  `GlossaryResolutionPacket` nodes and `HAS_GLOSSARY_RESOLUTION_PACKET` edges.
- The end-to-end proof output now summarizes queue health counts directly, and
  the MCP wrapper exposes `context_queue_health` and `context_glossary`.
- The end-to-end proof now calls `scripts/baltor_context_cache.py` against a
  temporary output directory and asserts the context cache, glossary cache, and
  `baltor.context_cache.write` audit event preserve source handles while
  blocking raw source dumps.

Latest cache-manifest proof:

- run ID: `adm-2f67310d56`
- context gateway result: `ctxr-adm-2f67310d56`
- context cache path:
  `/tmp/baltor-context-cache-proof-nxwnc8e1/runs/adm-2f67310d56.context.md`
- glossary cache path:
  `/tmp/baltor-context-cache-proof-nxwnc8e1/glossary/adm-2f67310d56.glossary.md`
- cache manifest path:
  `/tmp/baltor-context-cache-proof-nxwnc8e1/cache-manifest.json`
- cache audit path:
  `/tmp/baltor-context-cache-proof-nxwnc8e1/cache-writes.jsonl`
- manifest kind: `baltor.local-context-cache-manifest.v1`
- manifest entries: 1
- cache source handles: 11
- glossary resolution packets: 12
- queue trend during proof: `growing`, with estimated throughput available and
  zero queue-health warnings at proof time.

Latest repo-wiki connector proof:

- run ID: `adm-792f750b3d`
- connector-envelope proof run: `adm-0ef3202910`
- connector catalog count from MCP self-test: 9
- `repo_wiki` connector is present in the catalog and keeps
  `raw_source_access: fallback`.
- `repo_wiki` safety marks generated repo docs as derived context.
- `repo_wiki` sync policy includes post-commit hooks, push/MR webhooks,
  pipeline artifacts, file watchers, and scheduled polling, with
  commit-scoped outputs required.
- MCP self-test passed with `search_result_id: ctxr-adm-792f750b3d`.

Latest sync-contract endpoint proof:

- `/api/context-gateway/sync-contracts` returns
  `baltor.context-sync-contracts.v1`.
- It exposes `push`, `pull`, and `push_then_pull` modes, sync check gates,
  worker routing, repo-wiki artifact manifest kinds, connector trigger
  summaries, and commit-scoped output policy.
- MCP wrapper exposes the same contract as `context_sync_contracts`.
- Latest verified run: `adm-4f92a59602`.
- Latest connector-envelope proof run: `adm-6eac40e3bc`.
- Latest MCP self-test result: `sync_contract_kind:
  baltor.context-sync-contracts.v1`, `sync_trigger_count: 9`,
  `search_result_id: ctxr-adm-4f92a59602`.

Context object standards profile:

- `schemas/context-object.schema.json` defines
  `baltor.context-object.v1` for durable, auditable, source-linked context.
- `docs/architecture/baltor-context-object-standards.md` maps the profile to
  MCP delivery, LangChain-style runtime `contextSchema`, JSON Schema,
  JSON-LD/schema.org, W3C PROV, W3C Web Annotation, RO-Crate, SPDX/CycloneDX,
  OpenLineage, and OpenTelemetry.
- `/api/context-gateway/context-object-schema` returns
  `baltor.context-object-schema.v1` with the raw schema, standards mapping, and
  policy summary.
- MCP wrapper exposes the same contract as `context_object_schema`.
- `docs/architecture/baltor-context-object-graph-profile.md` now stores the
  broader graph-profile standard for versioning, artifacts, typed
  relationships, append-only lineage/history events, and task-specific packs.
- `/api/context-gateway/context-schema-catalog` returns
  `baltor.context-schema-catalog.v1` and advertises the context object graph
  schema family.
- `docs/architecture/baltor-context-fabric-product-blueprint.md` stores the
  product framing for Context Fabric: modules, interfaces, deployment models,
  standards mappings, packaging, MVP phases, and product invariants.
- `/api/context-gateway/product-surface` returns
  `baltor.context-product-surface.v1` and exposes the same product contract for
  MCP/API clients.
- Admin demo exports now include `context-objects`.
  - Export package type: `baltor.context-objects.v1`.
  - Internal record kind: `baltor.context-object-graph-records.v1`.
  - It materializes context objects, immutable versions, derived artifacts,
    typed relationships, source-linked assertions, dimension definitions,
    dimension values, append-only events, and a context pack projection from a
    run.
  - Context objects now carry namespaced flexible facets and a `five_w_one_h`
    projection, while custom numeric concepts such as operational risk,
    verifiability, freshness, sensitivity, prompt-injection risk, and
    actionability are first-class dimension records.
- `/api/context-gateway/dimensions` and MCP tool `context_dimensions` expose a
  bounded read-only view of dimension definitions and dimension values by run,
  dimension, or subject. Scores are explicitly treated as assessments, not
  source facts.
- `/admin-demo/explore` and `/admin-dashboard/monitor` now include a Dimension
  engine panel that surfaces top operational-risk objects and lowest
  verifiability objects from the latest context-object projection.
- `db/postgres/schema.sql` now includes Context Object Fabric persistence
  tables for objects, versions, relationships, assertions, dimension
  definitions, dimension values, artifacts, lineage events, and context packs,
  with JSONB indexes for facets/endpoints/scope and promoted indexes for
  relationship and dimension retrieval.
  - The DDL has been validated in a disposable `pgvector/pgvector:pg16`
    container with `psql -v ON_ERROR_STOP=1 -f /schema.sql`.
- Model routing is provider-neutral.
  - `/api/context-gateway/model-routing` and MCP tool
    `context_model_routing` expose capability slots, risk scoring, escalation
    thresholds, and a sample route decision.
  - Model families such as MiniMax, Kimi, DeepSeek, Mistral, Llama, Qwen,
    Gemma, GLM, Nemotron, Granite, and Jamba are examples inside slots, not
    hard-coded routing rules.
  - Latest local proof: `adm-4afc475a12`; context gateway result
    `ctxr-adm-4afc475a12`; MCP self-test reported 14 schema kinds, 7 model
    profiles, and sample recommended route `large_open`.
- Reranking is source-aware and separate from model routing.
  - `/api/context-gateway/reranking` and MCP tool `context_reranking` expose
    deterministic, lexical, vector, cross-encoder, LoRA/domain, LLM-judge, and
    human-review reranker stages.
  - LoRA/domain rerankers are represented as eval-gated adapter profiles with
    lineage and source handles, not as global truth or provider-specific rules.
  - Latest local proof: `adm-3ec53fd89f`; context gateway result
    `ctxr-adm-3ec53fd89f`; MCP self-test reported 16 schema kinds, 7 reranker
    profiles, and sample recommended stage
    `cross_encoder_then_lora_if_domain_adapter_available`.

TryCloudflare proof:

- demo URL returned HTTP 200 and contained six-card markers;
- gateway status URL returned HTTP 200 and contained
  `baltor-context-gateway`, `context_search`, and
  `retrieval_policy_owned_by_baltor`.
- heartbeat URL returned HTTP 200 and contained `baltor.debug_heartbeat.v1`;
- connector catalog URL returned HTTP 200 and contained `indexed_mirror_first`,
  `gitlab`, and `unrestricted_raw_tools_exposed: false`.
- queue-health URL returned HTTP 200 through TryCloudflare and included
  `baltor.queue-health.v1`, `trend`, `throughput`, `history`, and
  `recent_samples`.
- ownership context search through TryCloudflare returned dated ownership facts
  with event types, source handles, refresh risks, entity candidates,
  `ownership_change_records`, `ownership_conflict_groups`, and
  `ownership_refresh_jobs`.

An isolated async worker proof is now available:

```bash
python3 scripts/test_baltor_admin_demo_flow.py \
  --port 9316 \
  --isolated-worker \
  --wait-worker-seconds 120 \
  --worker-max-jobs 80
```

Latest isolated proof after connector/heartbeat expansion:

- run ID: `adm-8383f5130f`
- connector-envelope proof run: `adm-9125be74b6`
- upload type: nested ZIP
- extracted hierarchy: 5 folders, 5 files, 5 pages, 11 components
- worker records surfaced in monitor/API: 11
- per-run worker event records surfaced: 45
- node evidence records surfaced: 4
- proposed node edges surfaced: 4
- fresh follow-up jobs included `queued_at` timestamps and pending sample age
  telemetry; missing timestamp count was zero in the isolated queue.
- approval, budget-blocked, and permanent-failure queues: 0
- exports checked: manifest, text, RAG, graph, audit, safe-context,
  context-pack
- context records checked: RAG and graph exports include `ctx://baltor/...`
  handles; context-pack includes gateway policy and source handles
- gateway checked: context search returned 8 handles and fetch expanded a
  component handle
- isolated proof now queues and waits for the ZIP run before registering the
  connector-envelope run so the worker proof is not blocked behind connector
  follow-ups.

The remaining live-runtime gap is shared queue backlog under repeated proof
runs. The Docker worker is healthy and processing, holds remain zero, and the
monitor now distinguishes active/stale jobs, backlog trend, estimated drain
time, persisted queue-history state, and per-family queue throughput. The next
worker-focused loop should make the ownership event records richer by adding
canonical entity resolution and stronger contradiction/supersession scoring for
dated parent-vs-independent ownership records.
