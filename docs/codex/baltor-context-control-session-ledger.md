# Baltor Context-Control Session Ledger

This ledger is for long-running context-control/admin-demo work. Append concise
entries after each meaningful loop.

## 2026-06-01

- Added persistent context files for current state, iteration priorities, test
  plan, and long-run goal command.
- Captured the active local/TryCloudflare URLs, local worker stack, Ollama/Gemma
  route, Redis queue, worker ledger, and safety constraints.
- Current implementation work in progress:
  - surface all worker ledger artifacts in admin run state;
  - normalize LLM-proposed graph edge types;
  - add contract-specific exports;
  - add a self-contained ZIP upload proof test;
  - restart and verify the local admin server.

Next action:

- Continue the admin-demo implementation and test loop from
  `docs/codex/baltor-context-control-iteration-plan.md`.

## 2026-06-01 Continued

- Improved `scripts/baltor_admin_demo_server.py`:
  - added latest-run selection by `created_at`;
  - added run artifact counters for worker, node research, and LLM outputs;
  - added contract-specific export builders for manifest, text, RAG, graph,
    audit, and safe-context packages;
  - added a run inspector to `/admin-dashboard/monitor` showing hierarchy,
    queue job, artifact counts, recent worker records, local LLM status, and
    export links;
  - added artifact counts and latest run ID to `/api/admin-dashboard/events`;
  - added safe-context to the download page.
- Improved `scripts/context_workers/workers/llm_trust_layer.py`:
  - added controlled edge vocabulary for LLM-proposed graph edges;
  - normalized common edge aliases;
  - marked out-of-vocabulary edges as `REQUIRES_REVIEW` with promotion blocked.
- Added `scripts/test_baltor_admin_demo_flow.py`:
  - starts or targets an admin-demo server;
  - checks all six admin routes plus monitor;
  - uploads a nested ZIP with synthetic business/policy facts;
  - polls the run API;
  - verifies ZIP hierarchy metadata;
  - validates manifest, text, RAG, graph, audit, and safe-context exports.
- Restarted the updated demo on `http://127.0.0.1:9304`.
- Validation:
  - `python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/context_workers/workers/llm_trust_layer.py scripts/test_baltor_admin_demo_flow.py`
  - `python3 -m scripts.context_workers.runner --validate-manifest`
  - `python3 scripts/test_baltor_admin_demo_flow.py --port 9314`
  - `python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304`
- Latest proof run on port 9304:
  - run ID: `adm-51d424b933`;
  - ZIP hierarchy: 5 folders, 5 files, 5 pages, 11 components;
  - exports: audit, graph, manifest, rag, safe-context, text;
  - Redis queue available; approval, budget-blocked, and permanent-failure
    queues were zero;
  - context worker container healthy, with local LLM jobs actively processing.

Next action:

- Tighten the proof script so it optionally waits for worker ledger records and
  local LLM artifact counts when the context worker is not busy with an older
  local model job.

## 2026-06-01 MCP Gateway And Isolated Worker Proof

- Added `docs/architecture/baltor-mcp-context-gateway.md` from the architecture
  direction that Claude Code should be a client of a controlled MCP context
  gateway, not the primary retrieval brain.
  - Gateway responsibilities now include ACL filtering, hybrid search, ranking,
    compression, citations, source handles, audit, context-pack contracts, and
    live source fallback.
  - Initial MCP tools are specified: `context_search`, `context_fetch`,
    `context_expand`, `context_trace`, and `context_status`.
  - Raw Jira/Confluence/GitLab tools are explicitly fallback or gated live
    source actions, not default retrieval.
- Updated `docs/codex/baltor-context-control-iteration-plan.md` to include the
  MCP context gateway as an implementation priority.
- Updated `docs/architecture/llm-trust-layer.md` to clarify that local
  `llm.audit.review` downgrades to open-weight review unless frontier/human
  review is explicitly allowed.
- Fixed `scripts/baltor_admin_demo_server.py` after the status endpoint patch
  accidentally split `export_payload`; exports now return package dicts again.
- Updated `scripts/context_workers/runner.py` so `CONTEXT_WORKER_LEDGER` can
  override the worker ledger path. This enables isolated proof runs.
- Extended `scripts/test_baltor_admin_demo_flow.py`:
  - added `--wait-worker-seconds`;
  - added `--isolated-worker`;
  - added `--worker-max-jobs`;
  - starts a temporary server, isolated Redis queue, isolated Redis event
    stream, isolated upload directory, isolated ledger, and local worker;
  - asserts worker records/enrichment appear and approval/budget/failure queues
    remain zero.
- Rebuilt/restarted the Docker context worker after the local audit downgrade.
- Repaired two stale local demo audit jobs that were held by the old approval
  policy.

Validation:

```bash
python3 -m py_compile scripts/context_workers/runner.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_admin_demo_server.py scripts/context_workers/workers/llm_trust_layer.py
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/test_baltor_admin_demo_flow.py --port 9316 --isolated-worker --wait-worker-seconds 120 --worker-max-jobs 80
```

Latest isolated proof:

- run ID: `adm-b63d6c5601`
- ZIP hierarchy: 5 folders, 5 files, 5 pages, 11 components
- worker records: 11
- node evidence: 4
- proposed node edges: 4
- exports: audit, graph, manifest, rag, safe-context, text
- approval, budget-blocked, and permanent-failure queues: 0

Next action:

- Add `ctx://` source handles and typed context-pack export records so the demo
  starts behaving like the future MCP context gateway.

## 2026-06-01 Context Gateway HTTP Surface

- Added `ctx://baltor/...` source handles to RAG records, graph source/claim
  nodes, graph SUPPORTS evidence handles, safe-context records, and
  context-pack records.
- Added the `context-pack` export contract to the admin demo, download page,
  monitor export links, manifest export list, and proof script.
- Added local gateway functions in `scripts/baltor_admin_demo_server.py`:
  - `gateway_status_payload`;
  - `context_search_payload`;
  - `context_fetch_payload`;
  - `context_trace_payload`.
- Added local HTTP gateway endpoints:
  - `GET /api/context-gateway/status`;
  - `GET/POST /api/context-gateway/search`;
  - `GET/POST /api/context-gateway/fetch`;
  - `GET /api/context-gateway/trace`.
- Extended `scripts/test_baltor_admin_demo_flow.py` to prove:
  - gateway status is reachable;
  - gateway search returns a bounded context pack with `ctx://` handles;
  - gateway fetch expands one returned handle;
  - gateway trace preserves the policy that raw source access is fallback.
- Updated the MCP context gateway architecture, current-state, and test-plan
  docs to reflect the implemented local API surface.

Next action:

- Re-run py_compile, manifest validation, isolated worker proof, live 9304
  proof, and restart the public demo server if the live process is still on old
  code.

Validation completed:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/context_workers/runner.py scripts/context_workers/workers/llm_trust_layer.py
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/test_baltor_admin_demo_flow.py --port 9318 --isolated-worker --wait-worker-seconds 120 --worker-max-jobs 80
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
curl -L -sS -o /tmp/baltor-cloudflare-home.html -w "%{http_code} %{url_effective}\n" https://pepper-rolled-obligations-council.trycloudflare.com/admin-demo/
curl -L -sS -o /tmp/baltor-cloudflare-status.json -w "%{http_code} %{url_effective}\n" https://pepper-rolled-obligations-council.trycloudflare.com/api/context-gateway/status
```

Latest isolated proof:

- run ID: `adm-1392729c7e`
- ZIP hierarchy: 5 folders, 5 files, 5 pages, 11 components
- worker records: 11
- node evidence: 4
- proposed node edges: 4
- context gateway: `ctxr-adm-1392729c7e`, 8 handles, fetched one component
- exports: audit, context-pack, graph, manifest, rag, safe-context, text
- approval, budget-blocked, and permanent-failure queues: 0

Latest live proof:

- local URL: `http://127.0.0.1:9304/admin-demo/`
- monitor URL: `http://127.0.0.1:9304/admin-dashboard/monitor`
- TryCloudflare URL:
  `https://pepper-rolled-obligations-council.trycloudflare.com/admin-demo/`
- TryCloudflare gateway status:
  `https://pepper-rolled-obligations-council.trycloudflare.com/api/context-gateway/status`
- run ID: `adm-27c2bec87f`
- ZIP hierarchy: 5 folders, 5 files, 5 pages, 11 components
- worker records surfaced: 19
- node evidence surfaced: 12
- proposed node edges surfaced: 12
- context gateway: `ctxr-adm-27c2bec87f`, 8 handles, fetched one component
- exports: audit, context-pack, graph, manifest, rag, safe-context, text
- shared queue pending: 3
- approval, budget-blocked, and permanent-failure queues: 0
- Cloudflare HTTP checks: demo 200, gateway status 200

Next action:

- Add a small MCP server wrapper around the local gateway HTTP functions, then
  add source connector envelopes for Jira, Confluence, GitLab, and website
  mirrors without exposing raw unrestricted tools by default.

## 2026-06-01 MCP Wrapper

- Added `scripts/baltor_context_gateway_mcp.py`.
- The wrapper is zero-dependency and speaks JSON-RPC over stdio with
  Content-Length framing.
- Exposed tools:
  - `context_status`;
  - `context_search`;
  - `context_fetch`;
  - `context_trace`.
- The wrapper forwards calls to the local HTTP gateway endpoints instead of
  giving an agent direct raw access to source systems.
- Added `--self-test` to prove status/search/fetch/trace against a running
  local gateway.
- Added project-scoped `.mcp.json` registering `baltor-context-gateway` against
  `http://127.0.0.1:9304`.

Validation:

```bash
python3 -m py_compile scripts/baltor_context_gateway_mcp.py scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Self-test result:

- ok: true
- search result: `ctxr-adm-27c2bec87f`
- handle count: 4
- fetch kind: component
- tools: `context_status`, `context_search`, `context_fetch`,
  `context_trace`
- trace steps: 6

Next action:

- Add connector envelopes for Jira, Confluence, GitLab, and website mirrors
  under the same gateway policy.

## 2026-06-01 Connector Envelopes, Heartbeats, And Context Research

- Added governed connector envelopes to `scripts/baltor_admin_demo_server.py`.
  - Connector catalog now covers Jira, Confluence, GitLab, website, FTP/SFTP,
    Google Drive, SharePoint, and Git/S3 style mirrors.
  - Connector runs create `connector_envelope` source records with
    `ctx://baltor/...` handles, ACL-before-model policy, indexed-mirror-first
    retrieval policy, and raw-source fallback metadata.
  - Manifest, text, audit, graph, and context-pack exports now preserve
    connector envelopes.
  - Graph export now includes `ConnectorEnvelope` nodes and source mirror
    relationships.
- Added connector catalog HTTP contract:
  - `GET /api/context-gateway/connectors`
  - policy fields include `indexed_mirror_first`,
    `exact_handle_live_fetch_only`, and
    `unrestricted_raw_tools_exposed: false`.
- Added debug heartbeat contract:
  - `GET /api/debug/heartbeat`
  - `GET /api/admin-dashboard/heartbeat`
  - heartbeat kind: `baltor.debug_heartbeat.v1`
  - payload includes server uptime, run heartbeat, queue stats, latest worker
    event ID, worker ledger path/status, recent worker heartbeat files, latest
    events, and contract endpoints.
- Added per-run worker event-stream correlation so the heartbeat and run API can
  show `last_worker_event`, `recent_worker_events`, and
  `artifact_counts.worker_event_records` before slower ledger artifacts arrive.
- Updated monitor and run inspector UI to link heartbeat JSON and expose
  worker heartbeat/event-stream details.
- Extended `scripts/baltor_context_gateway_mcp.py`:
  - added `context_connectors`;
  - added `context_heartbeat`;
  - self-test now proves status, search, fetch, trace, connectors, and
    heartbeat.
- Extended `scripts/test_baltor_admin_demo_flow.py`:
  - checks `/api/context-gateway/connectors`;
  - checks `/api/debug/heartbeat`;
  - posts a GitLab connector-envelope run;
  - asserts connector export, graph, ACL, retrieval policy, and source handle
    contracts.
- Added `docs/research/enterprise-context-database-phases.md` summarizing
  public patterns for context database build phases:
  - gateway-first experimentation;
  - shared RAG/agent platforms;
  - enriched indexes and ABAC;
  - code-specific retrieval;
  - contextual retrieval and reranking;
  - MCP governance;
  - graph later, after ticket/MR/file/service relationships are common.
- Updated:
  - `.codex/prompts/baltor-context-control-goal.md`;
  - `docs/architecture/baltor-mcp-context-gateway.md`;
  - `docs/codex/baltor-context-control-current-state.md`;
  - `docs/codex/baltor-context-control-test-plan.md`.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
curl -L -sS -o /tmp/baltor-heartbeat.json -w "%{http_code}\n" https://pepper-rolled-obligations-council.trycloudflare.com/api/debug/heartbeat
curl -L -sS -o /tmp/baltor-connectors.json -w "%{http_code}\n" https://pepper-rolled-obligations-council.trycloudflare.com/api/context-gateway/connectors
```

Latest live proof:

- local URL: `http://127.0.0.1:9304/admin-demo/`
- monitor URL: `http://127.0.0.1:9304/admin-dashboard/monitor`
- TryCloudflare URL:
  `https://pepper-rolled-obligations-council.trycloudflare.com/admin-demo/`
- ZIP run ID: `adm-6877a1ce38`
- connector run ID: `adm-14cfa4a60a`
- connector handle:
  `ctx://baltor/run/connector/connector=gitlab/target=https-gitlab-example-com-context-control-baltor`
- ZIP hierarchy: 5 folders, 5 files, 5 pages, 11 components
- connector catalog: 8 connectors
- context gateway: `ctxr-adm-6877a1ce38`, 8 handles, fetched one component
- heartbeat: `baltor.debug_heartbeat.v1`, run stage `serve`, Redis available,
  latest worker event ID present
- exports: audit, context-pack, graph, manifest, rag, safe-context, text
- approval, budget-blocked, and permanent-failure queues: 0
- shared queue pending: 5
- TryCloudflare checks: heartbeat 200, connector catalog 200, gateway status
  200; content checks confirmed `baltor.debug_heartbeat.v1`,
  `last_worker_event`, `recent_worker_events`, `worker_event_records`,
  `latest_context_worker_event_id`, `indexed_mirror_first`, `gitlab`,
  `unrestricted_raw_tools_exposed: false`, `context_connectors`,
  `context_heartbeat`, and `retrieval_policy_owned_by_baltor`.

Open worker-focused gap:

- A later isolated proof with connector/heartbeat assertions created run
  `adm-fecc74697a`, saw 40 context-worker events, and kept approval/budget/
  permanent-failure queues at zero, but worker artifacts did not surface within
  the 120 second wait window while 7 jobs remained pending.
- The heartbeat contract now exposes the state needed to debug this without
  opening Redis or ledger files directly.

Next action:

- Correlate worker event-stream progress into run state earlier, or extend the
  isolated worker proof so local CPU LLM jobs have enough time to produce
  ledger artifacts after connector-envelope runs.

## 2026-06-01 Isolated Worker Proof Ordering Fix

- Updated `scripts/test_baltor_admin_demo_flow.py` so worker-wait mode queues
  the nested ZIP run before the connector-envelope run.
  - This keeps `--isolated-worker --wait-worker-seconds` focused on the ZIP
    pipeline instead of spending the wait window behind connector follow-ups.
  - Normal live smoke proof still checks connector envelopes, routes, exports,
    gateway search/fetch/trace, and heartbeat.
- Kept the per-run worker event heartbeat contract in the proof:
  - `last_worker_event`;
  - `recent_worker_events`;
  - `artifact_counts.worker_event_records`.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/test_baltor_admin_demo_flow.py --port 9320 --isolated-worker --wait-worker-seconds 120 --worker-max-jobs 80
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Latest isolated proof:

- run ID: `adm-c9dc412300`
- connector run ID: `adm-8e9a0a46df`
- ZIP hierarchy: 5 folders, 5 files, 5 pages, 11 components
- worker event records: 45
- worker records: 11
- node evidence: 4
- proposed node edges: 4
- context gateway: `ctxr-adm-c9dc412300`, 8 handles, fetched one component
- exports: audit, context-pack, graph, manifest, rag, safe-context, text
- approval, budget-blocked, and permanent-failure queues: 0

Latest live proof:

- local URL: `http://127.0.0.1:9304/admin-demo/`
- monitor URL: `http://127.0.0.1:9304/admin-dashboard/monitor`
- run ID: `adm-7d7d20594e`
- connector run ID: `adm-285412fb1f`
- context gateway: `ctxr-adm-7d7d20594e`, 8 handles, fetched one component
- MCP wrapper self-test: ok, 8 connectors, heartbeat kind
  `baltor.debug_heartbeat.v1`
- Docker context worker: healthy and processing queue events
- shared queue pending: 65
- approval, budget-blocked, and permanent-failure queues: 0

Next action:

- Add backlog-age and active-job telemetry to the heartbeat/monitor so the
  shared live queue can distinguish healthy slow local LLM backlog from stuck
  jobs.

## 2026-06-01 Backlog Telemetry And Child Job Timestamps

- Extended `queue_stats()` in `scripts/baltor_admin_demo_server.py`:
  - `oldest_pending_age_seconds`;
  - `newest_pending_age_seconds`;
  - `pending_sample`;
  - `pending_sample_missing_timestamps`;
  - `recent_worker_events`.
- Updated heartbeat proof assertions in `scripts/test_baltor_admin_demo_flow.py`
  to require queue backlog and recent worker event telemetry.
- Updated `scripts/context_workers/runner.py` so worker-emitted child jobs get
  `queued_at` at the actual child enqueue boundary.
- Rebuilt and restarted the Docker `context-worker` service so the shared live
  worker uses the same child-job timestamp contract.

Validation:

```bash
python3 -m py_compile scripts/context_workers/runner.py scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/test_baltor_admin_demo_flow.py --port 9322 --isolated-worker --wait-worker-seconds 120 --worker-max-jobs 80
sg docker -c 'docker compose -f infra/docker-compose.context.yml build context-worker'
sg docker -c 'docker compose -f infra/docker-compose.context.yml up -d context-worker'
sg docker -c 'docker compose -f infra/docker-compose.context.yml ps context-worker'
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
curl -L -sS -o /tmp/baltor-heartbeat.json -w "%{http_code} %{url_effective}\n" https://pepper-rolled-obligations-council.trycloudflare.com/api/debug/heartbeat
```

Latest isolated proof:

- run ID: `adm-8383f5130f`
- connector run ID: `adm-9125be74b6`
- worker event records: 45
- worker records: 11
- node evidence: 4
- proposed node edges: 4
- fresh pending sample had `queued_at` timestamps and
  `pending_sample_missing_timestamps: 0`
- approval, budget-blocked, and permanent-failure queues: 0

Latest live proof:

- run ID: `adm-77e227b079`
- connector run ID: `adm-bc2e348a1f`
- context gateway: `ctxr-adm-77e227b079`, 8 handles, fetched one component
- MCP wrapper self-test: ok, 8 connectors, heartbeat kind
  `baltor.debug_heartbeat.v1`
- Docker context worker rebuilt/restarted and healthy
- shared queue pending: 47
- shared pending sample has 10 inherited jobs without timestamps from the older
  worker contract; new isolated queues now prove timestamped child jobs
- approval, budget-blocked, and permanent-failure queues: 0
- TryCloudflare heartbeat 200 and exposes `pending_sample_missing_timestamps`,
  `recent_worker_events`, and `latest_context_worker_event_id`

Next action:

- Add active-job tracking to the worker event stream or admin correlation layer
  so the monitor can show "currently executing" jobs in addition to recent
  claimed/closed events and pending backlog.

## 2026-06-01 Active Worker Job Telemetry

- Added active job inference to `queue_stats()` in
  `scripts/baltor_admin_demo_server.py`.
  - The heartbeat now includes `active_worker_jobs` and
    `active_worker_job_count`, derived from recent `worker.job.claimed` and
    `worker.job.closed` events.
  - The queue payload still includes recent worker events, pending samples, and
    missing timestamp counts.
- Updated proof assertions so `/api/debug/heartbeat` must expose active worker
  job telemetry.
- Rebuilt/restarted the admin server on `9304` and verified the public
  TryCloudflare heartbeat exposes the new fields.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
curl -L -sS -o /tmp/baltor-heartbeat.json -w "%{http_code} %{url_effective}\n" https://pepper-rolled-obligations-council.trycloudflare.com/api/debug/heartbeat
```

Latest live proof:

- run ID: `adm-c2158b25b7`
- connector run ID: `adm-84b82b86a1`
- context gateway: `ctxr-adm-c2158b25b7`, 8 handles, fetched one component
- queue pending: 34
- active worker job count: 2
- pending sample missing timestamps: 10 inherited old jobs
- approval, budget-blocked, and permanent-failure queues: 0
- MCP wrapper self-test: ok, 8 connectors, heartbeat kind
  `baltor.debug_heartbeat.v1`
- TryCloudflare heartbeat: 200 and contains `active_worker_jobs`,
  `active_worker_job_count`, and `pending_sample_missing_timestamps`

Next action:

- Consider adding a small "Queue Health" panel to the monitor UI that renders
  active jobs and pending samples as rows instead of requiring users to inspect
  the raw heartbeat JSON.

## 2026-06-01 Monitor Queue Health UI

- Added `queue_health_panel()` to `scripts/baltor_admin_demo_server.py`.
  - `/admin-dashboard/monitor` now renders active worker jobs from
    `active_worker_jobs`.
  - It also renders a backlog sample from `pending_sample`, including unknown
    ages for inherited jobs that predate the timestamp contract.
  - Raw heartbeat JSON remains available for deeper inspection.
- Updated current-state and test-plan docs to require the Queue health section.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
curl -sS http://127.0.0.1:9304/admin-dashboard/monitor -o /tmp/baltor-monitor.html -w "%{http_code}\n"
grep -n "Queue health\\|Active worker jobs\\|Backlog sample" /tmp/baltor-monitor.html
```

Latest live proof:

- run ID: `adm-bfcb05405b`
- connector run ID: `adm-e897f22844`
- context gateway: `ctxr-adm-bfcb05405b`, 8 handles, fetched one component
- queue pending: 35
- active worker job count: 2
- approval, budget-blocked, and permanent-failure queues: 0
- monitor HTML contained `Queue health`, `Active worker jobs`, and
  `Backlog sample`.

Next action:

- Add an API-level queue-health contract if external monitors should consume
  the same UI-ready active/backlog rows without scraping monitor HTML.

## 2026-06-01 Queue Health API Contract

- Added `/api/admin-dashboard/queue-health`.
  - Package type: `baltor.queue-health.v1`
  - Includes summarized queue counts, active worker jobs, pending sample,
    recent worker events, and source stream.
- Added the route to `scripts/test_baltor_admin_demo_flow.py` so it is covered
  by the normal live proof.
- Updated current-state and test-plan docs.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
curl -sS http://127.0.0.1:9304/api/admin-dashboard/queue-health -o /tmp/baltor-queue-health.json -w "%{http_code}\n"
curl -L -sS -o /tmp/baltor-queue-health-cloud.json -w "%{http_code} %{url_effective}\n" https://pepper-rolled-obligations-council.trycloudflare.com/api/admin-dashboard/queue-health
```

Latest live proof:

- run ID: `adm-689050735a`
- connector run ID: `adm-41c66b414e`
- context gateway: `ctxr-adm-689050735a`, 8 handles, fetched one component
- queue-health endpoint: local 200 and TryCloudflare 200
- queue-health fields confirmed: `baltor.queue-health.v1`,
  `active_worker_job_count`, `pending_sample`, `recent_worker_events`
- queue pending: 37
- active worker job count: 2
- approval, budget-blocked, and permanent-failure queues: 0

Next action:

- Continue reducing shared live backlog visibility debt by showing worker task
  age thresholds or stale-active warnings when a claimed job remains open too
  long.

## 2026-06-01 Queue Stale Warning Thresholds

- Added explicit queue health thresholds to
  `scripts/baltor_admin_demo_server.py`:
  - `BALTOR_ACTIVE_WORKER_STALE_SECONDS`, default `300`;
  - `BALTOR_PENDING_JOB_STALE_SECONDS`, default `600`.
- Queue heartbeat and `/api/admin-dashboard/queue-health` now include:
  - `stale_active_worker_job_count`;
  - `stale_pending_job_count`;
  - `thresholds`;
  - `warnings`;
  - per-job `stale` and `stale_after_seconds` fields for active and pending
    samples.
- Monitor Queue health UI now marks stale active/pending rows and displays
  warning rows when thresholds are crossed.
- Updated proof assertions and test-plan docs to require stale warning fields.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
curl -sS http://127.0.0.1:9304/api/admin-dashboard/queue-health -o /tmp/baltor-queue-health.json -w "%{http_code}\n"
curl -L -sS -o /tmp/baltor-queue-health-cloud.json -w "%{http_code} %{url_effective}\n" https://pepper-rolled-obligations-council.trycloudflare.com/api/admin-dashboard/queue-health
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Latest live proof:

- run ID: `adm-653c74e27d`
- connector run ID: `adm-54c3d09001`
- context gateway: `ctxr-adm-653c74e27d`, 8 handles, fetched one component
- queue pending: 260
- active worker job count: 1
- stale active worker jobs: 0
- stale pending jobs: 0
- queue-health endpoint: local 200 and TryCloudflare 200
- queue-health fields confirmed: `baltor.queue-health.v1`, thresholds,
  warnings, stale active/pending counts
- MCP wrapper self-test: ok, 8 connectors, heartbeat kind
  `baltor.debug_heartbeat.v1`

Next action:

- Add the same queue-health contract to the MCP wrapper as a `context_queue_health`
  tool if coding agents should be able to check runtime health without calling
  raw HTTP endpoints.

## 2026-06-01 MCP Queue Health Tool

- Added `context_queue_health` to `scripts/baltor_context_gateway_mcp.py`.
  - It forwards to `/api/admin-dashboard/queue-health`.
  - It is read-only and returns `baltor.queue-health.v1`.
  - The MCP self-test now checks queue health alongside status, connectors,
    heartbeat, search, fetch, and trace.
- Updated:
  - `docs/architecture/baltor-mcp-context-gateway.md`;
  - `docs/codex/baltor-context-control-current-state.md`;
  - `docs/codex/baltor-context-control-test-plan.md`.

Validation:

```bash
python3 -m py_compile scripts/baltor_context_gateway_mcp.py scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Self-test result:

- ok: true
- tools: `context_status`, `context_search`, `context_fetch`,
  `context_trace`, `context_connectors`, `context_heartbeat`,
  `context_queue_health`
- queue health kind: `baltor.queue-health.v1`
- queue health warnings: 0
- connectors: 8
- heartbeat kind: `baltor.debug_heartbeat.v1`

Next action:

- Add a small queue-health regression assertion in the end-to-end proof output
  summary so the JSON proof reports active/stale counts directly, not only via
  nested queue payloads.

## 2026-06-01 Proof Queue Health Summary

- Updated `scripts/test_baltor_admin_demo_flow.py` so proof output includes a
  top-level `queue_health` summary:
  - `active_worker_job_count`;
  - `stale_active_worker_job_count`;
  - `stale_pending_job_count`;
  - `pending_sample_missing_timestamps`;
  - `warning_count`.
- This keeps the normal proof output readable while preserving the full nested
  queue payload for debugging.

Validation:

```bash
python3 -m py_compile scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Latest live proof:

- run ID: `adm-571e6369b8`
- connector run ID: `adm-1ce7008b97`
- context gateway: `ctxr-adm-571e6369b8`, 8 handles, fetched one component
- queue pending: 261
- active worker job count: 1
- stale active worker jobs: 0
- stale pending jobs: 0
- queue health warning count: 0
- pending sample missing timestamps: 0
- MCP queue health kind: `baltor.queue-health.v1`

Next action:

- Add lightweight queue-health history or trend sampling so the monitor can show
  whether backlog is shrinking, flat, or growing over time.

## 2026-06-01 Queue Health Trend Sampling

- Added in-process queue-health sample history to
  `scripts/baltor_admin_demo_server.py`.
  - Samples keep pending count, active worker count, stale active/pending
    counts, hold counts, and pending-age bounds.
  - Trend reports `unknown`, `flat`, `growing`, or `shrinking` from the rolling
    sample window, plus pending delta, active/stale deltas, sample count, and
    window length.
  - Stale thresholds and trend settings are controlled by constants/env knobs
    instead of copied literals.
- Extended `/api/debug/heartbeat`, `/api/admin-dashboard/events`, and
  `/api/admin-dashboard/queue-health` through the shared `queue_stats()` payload
  with `trend` and `recent_samples`.
- Updated the Queue health monitor panel to show trend status, pending delta,
  and sample count beside the active/stale/backlog metrics.
- Updated `scripts/test_baltor_admin_demo_flow.py` so heartbeat assertions and
  proof output include queue trend fields.
- Updated:
  - `docs/codex/baltor-context-control-current-state.md`;
  - `docs/codex/baltor-context-control-test-plan.md`;
  - `docs/architecture/baltor-mcp-context-gateway.md`.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 -m scripts.context_workers.runner --validate-manifest
fuser -k 9304/tcp
./.venv/bin/python scripts/baltor_admin_demo_server.py --port 9304
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
curl -sS https://pepper-rolled-obligations-council.trycloudflare.com/api/admin-dashboard/queue-health
```

Latest live proof:

- run ID: `adm-3735d5d68a`
- connector run ID: `adm-d07fbf193d`
- context gateway: `ctxr-adm-3735d5d68a`, 8 handles, fetched one component
- queue pending during proof: 242
- active worker job count: 1
- stale active worker jobs: 0
- stale pending jobs: 0
- queue health warning count: 0
- pending sample missing timestamps: 0
- proof trend status: `growing`, pending delta: 2, sample count: 7
- cloud queue-health route returned `baltor.queue-health.v1` with `trend` and
  `recent_samples`
- MCP queue health kind: `baltor.queue-health.v1`

Next action:

- Persist queue-health samples or add worker throughput/drain-time estimates so
  trend remains useful across admin-server restarts and long live backlogs.

## 2026-06-01 Queue Throughput And Drain Estimate

- Added queue throughput estimation to `scripts/baltor_admin_demo_server.py`.
  - Recent `worker.job.closed` stream events now produce a completion count,
    measurement window, jobs-per-minute rate, and estimated drain seconds.
  - The estimate has explicit `unknown`, `drained`, and `estimated` states, so
    the monitor does not invent drain times when Redis is unavailable or too
    few completions exist.
  - The minimum completion count is controlled by
    `BALTOR_QUEUE_THROUGHPUT_MIN_COMPLETIONS`.
- Surfaced throughput through:
  - `/api/debug/heartbeat`;
  - `/api/admin-dashboard/events`;
  - `/api/admin-dashboard/queue-health`;
  - the Queue health monitor panel as throughput and drain ETA pills.
- Updated `scripts/test_baltor_admin_demo_flow.py` so heartbeat assertions and
  the top-level proof `queue_health` summary include throughput status,
  jobs-per-minute, and estimated drain seconds.
- Updated:
  - `docs/codex/baltor-context-control-current-state.md`;
  - `docs/codex/baltor-context-control-test-plan.md`;
  - `docs/architecture/baltor-mcp-context-gateway.md`.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 -m scripts.context_workers.runner --validate-manifest
fuser -k 9304/tcp
./.venv/bin/python scripts/baltor_admin_demo_server.py --port 9304
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
curl -sS https://pepper-rolled-obligations-council.trycloudflare.com/api/admin-dashboard/queue-health
```

Latest live proof:

- run ID: `adm-6c725c62e3`
- connector run ID: `adm-5f0a5a6393`
- context gateway: `ctxr-adm-6c725c62e3`, 8 handles, fetched one component
- queue pending during proof: 242
- active worker job count: 1
- stale active worker jobs: 0
- stale pending sample jobs: 10
- queue health warning count: 1 (`stale_pending_job`)
- pending sample missing timestamps: 0
- proof trend status: `growing`, pending delta: 2, sample count: 5
- throughput status: `estimated`, jobs/minute: 4.125, estimated drain seconds:
  3520
- cloud queue-health route returned `baltor.queue-health.v1` with `trend`,
  `throughput`, and `recent_samples`
- MCP queue health kind: `baltor.queue-health.v1`

Next action:

- Persist queue-health samples across admin-server restarts, or split
  throughput by deterministic versus local-LLM task families so slow model
  reviews do not obscure fast queue-drain capacity.

## 2026-06-01 Persistent Queue Health History

- Added persisted queue-health sample history to
  `scripts/baltor_admin_demo_server.py`.
  - Samples append as JSONL to `dist/baltor-queue-health-history.jsonl` by
    default.
  - `BALTOR_QUEUE_HEALTH_HISTORY` can override the history path.
  - The admin server lazily loads up to the configured sample limit after
    restart before computing trend.
  - Duplicate unchanged samples are still suppressed by the existing
    `BALTOR_QUEUE_HEALTH_MIN_SAMPLE_SECONDS` gate.
- Surfaced persisted history metadata through the shared queue payload:
  - `history.path`;
  - `history.exists`;
  - `history.loaded`;
  - `history.sample_limit`;
  - `history.loaded_sample_count`.
- Updated `/api/admin-dashboard/queue-health`, `/api/debug/heartbeat`, the
  monitor Queue health panel, and proof output to include the history contract.
- Updated:
  - `docs/codex/baltor-context-control-current-state.md`;
  - `docs/codex/baltor-context-control-test-plan.md`;
  - `docs/architecture/baltor-mcp-context-gateway.md`.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 -m scripts.context_workers.runner --validate-manifest
fuser -k 9304/tcp
./.venv/bin/python scripts/baltor_admin_demo_server.py --port 9304
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
fuser -k 9304/tcp
./.venv/bin/python scripts/baltor_admin_demo_server.py --port 9304
curl -sS http://127.0.0.1:9304/api/admin-dashboard/queue-health
curl -sS https://pepper-rolled-obligations-council.trycloudflare.com/api/admin-dashboard/queue-health
```

Latest live proof:

- run ID: `adm-1bc568999e`
- connector run ID: `adm-f3cedbeda8`
- context gateway: `ctxr-adm-1bc568999e`, 8 handles, fetched one component
- queue pending during proof: 228
- active worker job count: 1
- stale active worker jobs: 0
- stale pending sample jobs: 10
- queue health warning count: 1 (`stale_pending_job`)
- pending sample missing timestamps: 0
- proof trend status: `growing`, pending delta: 2, sample count: 5
- throughput status: `estimated`, jobs/minute: 4.131, estimated drain seconds:
  3312
- persisted history existed and loaded 5 samples during proof output; after
  restart, local and TryCloudflare queue-health both reported
  `history.exists: true` and `history.loaded_sample_count: 8`
- MCP queue health kind: `baltor.queue-health.v1`

Next action:

- Split queue throughput by task family so deterministic work, node research,
  and local-LLM review each get separate rates and drain estimates.

## 2026-06-01 Task-Family Throughput And Ownership Scenario

- Added task-family classification to queue telemetry in
  `scripts/baltor_admin_demo_server.py`.
  - Worker events and pending sample rows now include `task_family`.
  - Pending jobs are scanned up to `BALTOR_QUEUE_PENDING_FAMILY_SCAN_LIMIT`
    and counted by family.
  - Queue throughput now includes `throughput.by_family`, with pending count,
    completion count, jobs-per-minute, and drain ETA per family.
  - The monitor renders a "Throughput by task family" section.
- Added a temporal company-ownership proof scenario:
  - `company/ownership/employment-agency-network.md` in the synthetic ZIP;
  - sample text also references staffing agency acquisition, merger, split,
    independent-ownership export, source-date requirement, and refresh need.
- The ownership scenario covers employment agencies being acquired, merged,
  split into a new entity, and later reported with conflicting current
  ownership. It is intentionally time-sensitive so downstream graph/context
  logic must not flatten it into timeless ownership.
- Updated:
  - `docs/codex/baltor-context-control-current-state.md`;
  - `docs/codex/baltor-context-control-test-plan.md`;
  - `docs/architecture/baltor-mcp-context-gateway.md`.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 -m scripts.context_workers.runner --validate-manifest
fuser -k 9304/tcp
./.venv/bin/python scripts/baltor_admin_demo_server.py --port 9304
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
curl -sS https://pepper-rolled-obligations-council.trycloudflare.com/api/admin-dashboard/queue-health
```

Latest live proof:

- run ID: `adm-2bd01b4f89`
- connector run ID: `adm-cc79889871`
- context gateway: `ctxr-adm-2bd01b4f89`, 10 handles, fetched one component
- ZIP hierarchy: 6 folders, 6 files, 6 pages, 18 components
- queue pending during proof: 209
- active worker job count: 1
- stale active worker jobs: 0
- stale pending sample jobs: 10
- queue health warning count: 1 (`stale_pending_job`)
- trend status: `shrinking`, pending delta: -19, sample count: 10
- throughput status: `estimated`, jobs/minute: 3.973, estimated drain seconds:
  3156
- throughput families: `context_gateway`, `deterministic_pipeline`,
  `local_llm_review`, `node_research`
- cloud queue-health route returned the same `throughput.by_family`,
  `pending_family_counts`, and persisted history fields.

Next action:

- Add first-class ownership-change claim/event typing so acquisition, merger,
  split/spinout, and current-owner claims become temporal graph candidates with
  source dates and safe-context caveats.

## 2026-06-01 Ownership-Change Claim And Graph Contract

- Added first-class ownership-change metadata in
  `scripts/baltor_admin_demo_server.py`.
  - Centralized claim construction through `build_claim_record(...)` so normal
    runs, sync demo runs, and worker-ledger sync use the same claim contract.
  - Ownership facts now carry `claim_type: ownership_change`, detected dates,
    `temporal_fragility`, `requires_refresh`, `safe_context_instruction`, and
    an embedded `ownership_change` record.
  - Event classification covers `acquisition`, `merger`, `split_or_spinout`,
    `current_parent_record`, `independent_ownership_record`, and
    `ownership_conflict_or_refresh_notice`.
  - Current parent and independent-ownership records are flagged for refresh so
    the context layer does not flatten dated supplier/vendor records into
    current ownership facts.
- Added ownership events to exports and context surfaces.
  - Manifest, text, graph, safe-context, context-pack, and audit exports expose
    `ownership_change_records`.
  - Graph export creates `OwnershipChangeEvent` nodes and
    `PROPOSES_OWNERSHIP_EVENT` edges, both evidence-linked and
    `promotion_allowed: false`.
  - Context search facts include ownership event type, temporal fragility,
    refresh requirement, and source-date-safe instructions.
  - Context-pack risks include explicit warnings for time-sensitive ownership
    records that need refresh before being stated as current.
- Updated the proof test to require ownership events end to end.
  - The synthetic ZIP must produce at least acquisition, merger, independent
    ownership, and refresh-required ownership records.
  - Graph, safe-context, and context-pack exports must expose ownership records.
  - Proof output now reports event types and refresh-required ownership count.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 -m scripts.context_workers.runner --validate-manifest
fuser -k 9304/tcp
./.venv/bin/python scripts/baltor_admin_demo_server.py --port 9304
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
curl -sS https://pepper-rolled-obligations-council.trycloudflare.com/api/admin-dashboard/queue-health
curl -sS 'https://pepper-rolled-obligations-council.trycloudflare.com/api/context-gateway/search?query=ownership%20CareShift%20Northstar%20parent%20independent'
```

Latest live proof:

- run ID: `adm-d24f5d0dbf`
- connector run ID: `adm-39bd33974e`
- context gateway: `ctxr-adm-d24f5d0dbf`, 10 handles, fetched one component
- ZIP hierarchy: 6 folders, 6 files, 6 pages, 18 components
- ownership records: 6
- ownership event types: `acquisition`, `current_parent_record`,
  `independent_ownership_record`, `merger`,
  `ownership_conflict_or_refresh_notice`, `split_or_spinout`
- ownership records requiring refresh: 3
- queue pending during proof: 196
- active worker job count: 1
- stale active worker jobs: 0
- stale pending sample jobs: 10
- queue health warning count: 1 (`stale_pending_job`)
- trend status: `shrinking`, pending delta: -13, sample count: 10
- throughput status: `estimated`, jobs/minute: 3.638, estimated drain seconds:
  3233
- throughput families: `context_gateway`, `deterministic_pipeline`,
  `local_llm_review`, `node_research`
- MCP self-test passed with `queue_health_kind: baltor.queue-health.v1`.
- TryCloudflare ownership search returned ownership facts with event types,
  refresh risks, source handles, and `ownership_change_records`.

Next action:

- Add entity candidate extraction for ownership records and generate
  supersession/conflict groups when newer dated ownership records disagree with
  older parent-company records.

## 2026-06-01 Ownership Entity Candidates And Conflict Groups

- Added deterministic entity candidates to ownership-change records.
  - Acquisition records now identify acquirer and acquired organization
    candidates.
  - Merger records identify merging organizations and the resulting
    organization candidate.
  - Split/spinout records identify resulting entity and source-division
    candidates.
  - Current parent and independent-ownership records identify the owned entity
    so current-status claims can be compared.
- Added `ownership_conflict_groups`.
  - Dated current-status records for the same owned entity are grouped when
    event types disagree, for example `current_parent_record` vs
    `independent_ownership_record`.
  - The synthetic proof now creates
    `ownership-conflict:careshift-partners`, linking `fact-009` dated
    2025-11-20 and `fact-010` dated 2026-02-10.
  - Context-pack risks now warn that these records conflict or supersede each
    other and require refresh before stating current ownership.
- Added graph contract support.
  - Graph export creates `OwnershipConflictGroup` nodes.
  - Claim nodes connect to conflict groups through
    `HAS_OWNERSHIP_CONFLICT` edges.
  - These graph additions remain `promotion_allowed: false`.
- Updated docs:
  - `docs/codex/baltor-context-control-current-state.md`;
  - `docs/codex/baltor-context-control-test-plan.md`;
  - `docs/architecture/baltor-mcp-context-gateway.md`.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
fuser -k 9304/tcp
./.venv/bin/python scripts/baltor_admin_demo_server.py --port 9304
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
curl -sS 'https://pepper-rolled-obligations-council.trycloudflare.com/api/context-gateway/search?query=ownership%20CareShift%20Northstar%20parent%20independent'
```

Latest live proof:

- run ID: `adm-ef40f34541`
- connector run ID: `adm-d275a1fdbc`
- context gateway: `ctxr-adm-ef40f34541`, 10 handles, fetched one component
- ZIP hierarchy: 6 folders, 6 files, 6 pages, 18 components
- ownership records: 6
- ownership conflict groups: 1
- conflict group target: `CareShift Partners`
- linked conflict claims: `fact-009`, `fact-010`
- ownership records requiring refresh: 3
- queue pending during proof: 197
- active worker job count: 1
- stale active worker jobs: 0
- stale pending sample jobs: 10
- queue health warning count: 1 (`stale_pending_job`)
- trend status: `growing`, pending delta: 3, sample count: 10
- throughput status: `estimated`, jobs/minute: 3.41, estimated drain seconds:
  3466
- MCP self-test passed with `search_result_id: ctxr-adm-ef40f34541`.
- TryCloudflare context search returned `ownership_change_records`,
  `ownership_conflict_groups`, and a specific risk for
  `ownership-conflict:careshift-partners`.

Next action:

- Add adapter-backed refresh planning for business ownership records, then add
  stronger scoring for whether a newer independent-ownership record supersedes
  an older parent-company record or remains an unresolved conflict.

## 2026-06-01 Ownership Refresh Planning

- Added adapter-backed refresh planning for time-sensitive ownership records in
  `scripts/baltor_admin_demo_server.py`.
  - Reused `scripts.context_workers.priority.make_research_task(...)` so
    ownership refresh jobs carry the same task, lane, priority, queue policy,
    cost estimate, and budget policy as the worker system.
  - Current parent and independent-ownership records now produce
    `ownership_current_status_refresh` jobs.
  - Dated current-status conflict groups now produce
    `ownership_conflict_reconciliation` jobs.
  - Ownership refresh jobs use `context.search.verify` and include an
    `adapter_plan` that keeps `person_level_osint: disabled` while allowing
    configured non-PII business public-record sources.
  - Context packs expose `ownership_refresh_jobs`; audit and safe-context
    exports expose `refresh_jobs`.
- Fixed direct script launch after adding the worker priority import by adding
  the repository root to `sys.path` before importing `scripts.*` modules.
- Updated proof assertions in `scripts/test_baltor_admin_demo_flow.py`.
  - Ownership refresh jobs must exist.
  - The conflict reconciliation refresh job must exist.
  - Ownership refresh jobs must preserve the privacy gate and use
    `context.search.verify`.
  - Audit export must include ownership refresh jobs.
- Updated docs:
  - `docs/codex/baltor-context-control-current-state.md`;
  - `docs/codex/baltor-context-control-test-plan.md`;
  - `docs/architecture/baltor-mcp-context-gateway.md`.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
fuser -k 9304/tcp
./.venv/bin/python scripts/baltor_admin_demo_server.py --port 9304
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
curl -sS 'https://pepper-rolled-obligations-council.trycloudflare.com/api/context-gateway/search?query=ownership%20CareShift%20Northstar%20parent%20independent'
curl -sS http://127.0.0.1:9304/api/admin-demo/runs/adm-f991928ac1/exports/audit
```

Latest live proof:

- run ID: `adm-f991928ac1`
- connector run ID: `adm-0667c8309c`
- context gateway: `ctxr-adm-f991928ac1`, 10 handles, fetched one component
- ZIP hierarchy: 6 folders, 6 files, 6 pages, 18 components
- ownership records: 6
- ownership conflict groups: 1
- ownership refresh jobs: 4
- ownership records requiring refresh: 3
- conflict reconciliation job: `ownership-conflict:careshift-partners`
- queue pending during proof: 178
- active worker job count: 1
- stale active worker jobs: 0
- stale pending sample jobs: 10
- queue health warning count: 1 (`stale_pending_job`)
- trend status: `shrinking`, pending delta: -17, sample count: 10
- throughput status: `estimated`, jobs/minute: 3.188, estimated drain seconds:
  3350
- MCP self-test passed with `search_result_id: ctxr-adm-f991928ac1`.
- TryCloudflare context search returned `ownership_refresh_jobs` with
  queue/budget policy metadata and privacy-safe adapter plans.

Next action:

- Add deterministic supersession scoring for ownership conflict groups, so a
  newer independent-ownership record can be marked as likely superseding an
  older parent-company record while still requiring refresh before current use.

## 2026-06-01 Ownership Supersession Scoring

- Added deterministic supersession scoring for dated ownership conflict groups.
  - The `CareShift Partners` conflict group now records
    `latest_claim_id: fact-010` for the 2026-02-10 independent-ownership
    source.
  - The older 2025-11-20 parent-company source is listed in
    `superseded_claim_ids: [fact-009]`.
  - The group carries `resolution_suggestion:
    newer_independent_record_likely_supersedes_parent_record` and
    `supersession_confidence: 0.68`.
  - The suggestion is not a verification decision. Context packs still require
    refresh before stating current ownership.
- Exposed supersession metadata through context packs and risk text.
- Added graph export edge support:
  - `claim:fact-010 MAY_SUPERSEDE_OWNERSHIP_CLAIM claim:fact-009`
  - `confidence: 0.68`
  - `promotion_allowed: false`
- Updated proof assertions in `scripts/test_baltor_admin_demo_flow.py`.
  - Conflict group must include the supersession suggestion.
  - Conflict group must identify the latest and candidate-superseded claims.
  - Graph export must include the `MAY_SUPERSEDE_OWNERSHIP_CLAIM` edge.
- Updated docs:
  - `docs/codex/baltor-context-control-current-state.md`;
  - `docs/codex/baltor-context-control-test-plan.md`;
  - `docs/architecture/baltor-mcp-context-gateway.md`.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
curl -sS 'https://pepper-rolled-obligations-council.trycloudflare.com/api/context-gateway/search?query=ownership%20CareShift%20Northstar%20parent%20independent'
python3 -c "import json,urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:9304/api/admin-demo/runs/adm-0448ccd85b/exports/graph')); edges=data.get('edges',[]); print(json.dumps([e for e in edges if e.get('type')=='MAY_SUPERSEDE_OWNERSHIP_CLAIM'][:5], indent=2)); print('count', sum(1 for e in edges if e.get('type')=='MAY_SUPERSEDE_OWNERSHIP_CLAIM'))"
```

Latest live proof:

- run ID: `adm-0448ccd85b`
- connector run ID: `adm-3c8c7edda4`
- context gateway: `ctxr-adm-0448ccd85b`, 10 handles, fetched one component
- ZIP hierarchy: 6 folders, 6 files, 6 pages, 18 components
- ownership records: 6
- ownership conflict groups: 1
- ownership refresh jobs: 4
- conflict group target: `CareShift Partners`
- latest ownership claim: `fact-010`
- candidate-superseded ownership claim: `fact-009`
- supersession suggestion:
  `newer_independent_record_likely_supersedes_parent_record`
- supersession confidence: `0.68`
- graph supersession edges: 1
- ownership records requiring refresh: 3
- queue pending during proof: 180
- active worker job count: 1
- stale active worker jobs: 0
- stale pending sample jobs: 10
- queue health warning count: 1 (`stale_pending_job`)
- trend status: `growing`, pending delta: 3, sample count: 10
- throughput status: `estimated`, jobs/minute: 3.106, estimated drain seconds:
  3478
- worker manifest validation passed with 88 workers.
- MCP self-test passed with `search_result_id: ctxr-adm-0448ccd85b`.
- TryCloudflare context search returned `ownership_change_records`,
  `ownership_conflict_groups`, `ownership_refresh_jobs`, and the
  supersession suggestion in the risk list.

Next action:

- Add a bounded `/api/context-gateway/reconcile` or worker-readable
  reconciliation artifact that turns ownership conflict groups plus refresh
  plans into an explicit adjudication packet for local LLM/human review.

## 2026-06-01 Term Clarity Concern Detection

- Added deterministic terminology-clarity detection to
  `scripts/baltor_admin_demo_server.py`.
  - `MULTI_MEANING_TERM`: terms whose local text explicitly says they may have
    multiple meanings.
  - `UNDEFINED_DOMAIN_TERM`: known business/domain terms used without a
    source-local definition.
  - `ACRONYM_WITHOUT_DEFINITION`: all-caps acronyms that are not defined in the
    document.
- Added a `policies/vendor-terms.md` proof document to the synthetic ZIP.
  - `agency` is detected as a multi-meaning term.
  - `active vendor` is detected as an undefined domain term.
  - `CCO` is detected as an acronym without definition.
- Exposed term clarity records through:
  - run summary and artifact counts;
  - manifest, text, graph, audit, safe-context, and context-pack exports;
  - context-pack risks;
  - graph `TermClarityConcern` nodes and `HAS_TERM_CLARITY_CONCERN` edges.
- Updated proof assertions in `scripts/test_baltor_admin_demo_flow.py`.
  - The run must include term clarity concerns.
  - The graph export must include term concern nodes and edges.
  - Safe-context and context-pack exports must include term clarity concerns.
- Updated docs:
  - `docs/codex/baltor-context-control-current-state.md`;
  - `docs/codex/baltor-context-control-test-plan.md`;
  - `docs/architecture/baltor-mcp-context-gateway.md`.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
fuser -k 9304/tcp
./.venv/bin/python scripts/baltor_admin_demo_server.py --port 9304
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
curl -sS 'https://pepper-rolled-obligations-council.trycloudflare.com/api/context-gateway/search?query=agency%20active%20vendor%20CCO%20affiliate%20partner%20term%20definition'
```

Latest live proof:

- run ID: `adm-6a796dfcf1`
- connector run ID: `adm-2662b7f032`
- context gateway: `ctxr-adm-6a796dfcf1`, 10 handles, fetched one component
- ZIP hierarchy: 6 folders, 7 files, 7 pages, 22 components
- ownership records: 6
- ownership conflict groups: 1
- ownership refresh jobs: 4
- term clarity concerns: 12
- term concern types: `ACRONYM_WITHOUT_DEFINITION`, `MULTI_MEANING_TERM`,
  `UNDEFINED_DOMAIN_TERM`
- queue pending during proof: 150
- active worker job count: 1
- stale active worker jobs: 0
- stale pending sample jobs: 10
- queue health warning count: 1 (`stale_pending_job`)
- trend status: `shrinking`, pending delta: -15, sample count: 10
- throughput status: `estimated`, jobs/minute: 3.094, estimated drain seconds:
  2908
- worker manifest validation passed with 88 workers.
- MCP self-test passed with `search_result_id: ctxr-adm-6a796dfcf1`.
- TryCloudflare context search returned term-specific risks and
  `term_clarity_concerns` for `agency`, `active vendor`, and `CCO`.

Next action:

- Add glossary resolution packets: unresolved term concerns should be routable
  to a local LLM glossary reviewer or a human glossary owner, and resolved terms
  should create source-scoped glossary entries rather than global facts.

## 2026-06-01 Glossary Resolution Packets And Local Skill Kit

- Added source-scoped glossary resolution packets to
  `scripts/baltor_admin_demo_server.py`.
  - Each `term_clarity_concern` now creates a
    `baltor.glossary-resolution-packet.v1` packet.
  - Packets include `term`, `concern_id`, `concern_type`, evidence,
    possible meanings, linked claim IDs, review routes, a proposed
    source-local glossary entry, and safe-context policy.
  - Safe-context policy blocks global memory promotion and canonical graph
    promotion until a term is reviewed.
- Added a dedicated glossary export:
  - `/api/admin-demo/runs/<run_id>/exports/glossary`
  - package type `baltor.glossary.v1`
- Added gateway glossary API:
  - `GET /api/context-gateway/glossary?term=agency`
  - `POST /api/context-gateway/glossary`
  - response kind `baltor.context-glossary.v1`
- Added MCP wrapper support:
  - new tool: `context_glossary`
  - self-test checks glossary packet count and kind.
- Added graph contract:
  - `GlossaryResolutionPacket` nodes
  - `HAS_GLOSSARY_RESOLUTION_PACKET` edges
  - `promotion_allowed: false`
- Added a local Claude Code skill:
  - `.claude/skills/baltor-context-gateway/SKILL.md`
  - The skill tells agents to prefer Baltor context tools, keep local memory
    source-linked, and avoid raw source dumps.
- Added local client/SDK path documentation:
  - `docs/codex/baltor-claude-code-context-kit.md`
- Updated docs:
  - `docs/codex/baltor-context-control-current-state.md`;
  - `docs/codex/baltor-context-control-test-plan.md`;
  - `docs/architecture/baltor-mcp-context-gateway.md`.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
fuser -k 9304/tcp
./.venv/bin/python scripts/baltor_admin_demo_server.py --port 9304
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
curl -sS 'https://pepper-rolled-obligations-council.trycloudflare.com/api/context-gateway/glossary?term=agency'
```

Latest live proof:

- run ID: `adm-c3fe067845`
- connector run ID: `adm-efc0841f21`
- context gateway: `ctxr-adm-c3fe067845`, 10 handles, fetched one component
- ZIP hierarchy: 6 folders, 7 files, 7 pages, 22 components
- ownership records: 6
- ownership conflict groups: 1
- ownership refresh jobs: 4
- term clarity concerns: 12
- glossary resolution packets: 12
- filtered glossary gateway packet count for `agency`: 1
- exports: audit, context-pack, glossary, graph, manifest, RAG, safe-context,
  text
- queue pending during proof: 149
- active worker job count: 1
- stale active worker jobs: 0
- stale pending sample jobs: 10
- queue health warning count: 1 (`stale_pending_job`)
- trend status: `flat`, pending delta: 1, sample count: 10
- throughput status: `estimated`, jobs/minute: 3.044, estimated drain seconds:
  2937
- worker manifest validation passed with 88 workers.
- MCP self-test passed with `search_result_id: ctxr-adm-c3fe067845`,
  `glossary_kind: baltor.context-glossary.v1`, and
  `glossary_packet_count: 3`.
- TryCloudflare glossary search returned `glossary-001` for `agency`, including
  possible meanings, source-local proposed glossary entry, review routes, and
  promotion blocks.

Next action:

- Add a small local memory/cache writer for approved context packs and glossary
  packets under a configured local directory, with source handles and no raw
  source dumps.

## 2026-06-01 Local Context Cache Writer

- Added `scripts/baltor_context_cache.py`.
  - Calls `/api/context-gateway/search` and `/api/context-gateway/glossary`.
  - Writes compact Markdown cache files under `dist/baltor-context-cache/` by
    default.
  - Stores facts, risks, source handles, glossary packets, and cache policy.
  - Does not mirror raw source documents.
- Updated `docs/codex/baltor-claude-code-context-kit.md` to include the cache
  writer as the local SDK/client path after Obsidian or plain Markdown memory.

Validation:

```bash
python3 -m py_compile scripts/baltor_context_cache.py
python3 scripts/baltor_context_cache.py --base-url http://127.0.0.1:9304 --query 'agency active vendor CCO ownership'
sed -n '1,120p' dist/baltor-context-cache/INDEX.md
sed -n '1,180p' dist/baltor-context-cache/runs/adm-c3fe067845.context.md
sed -n '1,160p' dist/baltor-context-cache/glossary/adm-c3fe067845.glossary.md
```

Latest cache proof:

- run ID: `adm-c3fe067845`
- context cache:
  `dist/baltor-context-cache/runs/adm-c3fe067845.context.md`
- glossary cache:
  `dist/baltor-context-cache/glossary/adm-c3fe067845.glossary.md`
- index:
  `dist/baltor-context-cache/INDEX.md`
- fact count: 6
- glossary packet count: 12
- cache policy: source handles only, no raw source dumps, volatile facts require
  dates/refresh, glossary packets stay source-scoped until reviewed.

- Added `.claude/commands/baltor-cache-context.md` so Claude Code users can run
  the cache writer as a simple slash workflow.
- The cache writer now appends `baltor.context_cache.write` JSONL audit events.

Follow-up proof:

- `python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304`
  now exercises the cache writer inside an isolated temporary output directory.
- Latest cache-inclusive proof run: `adm-09839f7e83`.
- Verified cache artifacts:
  `/tmp/baltor-context-cache-proof-86fcmdb0/runs/adm-09839f7e83.context.md`,
  `/tmp/baltor-context-cache-proof-86fcmdb0/glossary/adm-09839f7e83.glossary.md`,
  and `/tmp/baltor-context-cache-proof-86fcmdb0/cache-writes.jsonl`.
- The proof asserts source handles are retained, raw source dumps remain
  blocked, `agency` glossary packets stay source-scoped, and the audit policy
  records `stores_raw_source_dump: false`.

Next action:

- Add a small `/goal`-oriented prompt contract that tells long-running agents
  how to alternate between gateway changes, cache/memory checks, heartbeat
  checks, and regression proofs without drifting into raw source dumps.

## 2026-06-01 Local Context SDK And Cache Manifest

- Added `scripts/baltor_context_client.py` as a dependency-free local client
  for the Baltor context gateway.
  - Exposes reusable `status`, `search`, `fetch`, `trace`, `connectors`,
    `glossary`, `heartbeat`, and `queue_health` methods.
  - Keeps Claude Code commands, hooks, cache writers, and future local sync
    tools from duplicating path/request-shape constants.
- Updated `scripts/baltor_context_cache.py`.
  - Uses the local client/SDK shim.
  - Supports direct execution as `python3 scripts/baltor_context_cache.py`.
  - Writes `cache-manifest.json` with kind
    `baltor.local-context-cache-manifest.v1`.
  - Links each cache write to context path, glossary path, audit log, source
    handle count, glossary packet count, and no-raw-source policy.
- Updated the end-to-end proof to assert the cache manifest exists, has the
  expected kind, points at the latest run, retains the no-raw-dump and
  source-handle policy, and is linked from the JSONL audit record.

Validation:

```bash
python3 -m py_compile scripts/baltor_context_client.py scripts/baltor_context_cache.py scripts/test_baltor_admin_demo_flow.py
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/baltor_context_cache.py --base-url http://127.0.0.1:9304 --query 'agency active vendor CCO ownership sdk sync manifest' --out-dir /tmp/baltor-context-cache-sdk-proof
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Latest proof:

- run ID: `adm-2f67310d56`
- context gateway result: `ctxr-adm-2f67310d56`
- cache manifest:
  `/tmp/baltor-context-cache-proof-nxwnc8e1/cache-manifest.json`
- manifest kind: `baltor.local-context-cache-manifest.v1`
- manifest entry count: 1
- source handles cached: 11
- glossary packets cached: 12
- queue health warnings: 0
- MCP self-test passed with `context_glossary`, `context_queue_health`, and
  heartbeat contracts healthy.

Next action:

- Add a small local sync/read command that reads `cache-manifest.json` and
  prints the latest cache summary for Obsidian/Basic Memory/Claude-Mem style
  consumers without contacting the gateway.

## 2026-06-01 Offline Cache Status Command

- Added `scripts/baltor_context_cache_read.py`.
  - Reads a local `cache-manifest.json`.
  - Validates kind `baltor.local-context-cache-manifest.v1`.
  - Prints either Markdown or JSON summary output.
  - Does not contact the context gateway or source systems.
- Added `.claude/commands/baltor-cache-status.md`.
  - Provides a simple Claude Code slash workflow for inspecting the latest
    cached context pack, glossary cache, audit log, and local memory policy.
- Updated `.claude/skills/baltor-context-gateway/SKILL.md` and
  `docs/codex/baltor-claude-code-context-kit.md` to document the offline
  status/read path.

Validation:

```bash
python3 -m py_compile scripts/baltor_context_cache_read.py
python3 scripts/baltor_context_cache_read.py --out-dir /tmp/baltor-context-cache-sdk-proof --format json
python3 scripts/baltor_context_cache_read.py --out-dir /tmp/baltor-context-cache-sdk-proof --include-entries 2
```

Latest offline read proof:

- manifest path:
  `/tmp/baltor-context-cache-sdk-proof/cache-manifest.json`
- latest run: `adm-09839f7e83`
- entry count: 1
- policy:
  `stores_raw_source_dump: false`, `stores_source_handles: true`,
  `glossary_packets_source_scoped: true`,
  `blocks_global_memory_promotion: true`.

Next action:

- Add a small hook/audit template for teams that want to run
  `/baltor-cache-context` after `context_search` and `/baltor-cache-status`
  at session start without making local memory authoritative.

## 2026-06-01 Repo Wiki Context Tool Research

- Added `docs/research/repo-wiki-context-tools.md`.
- Researched DeepWiki-like repo documentation and code-context tools:
  DeepWiki/Ask Devin, DeepWiki MCP, DeepWiki-Open, OpenDeepWiki, RepoWiki,
  RepoAgent, CodeWiki, repowise, Synthadoc, karpathy-llm-wiki, SwarmVault, and
  DeepWiki Markdown exporters.
- Classified them as repo-context compilers, not enterprise context
  authorities.
- Defined a provider-neutral Baltor adapter concept:
  `repo_wiki_status`, `repo_wiki_generate`, `repo_wiki_search`,
  `repo_wiki_fetch`, and `repo_wiki_manifest`.
- Added a normalized `baltor.repo-wiki-page.v1` target shape with repo/ref,
  commit SHA, generated timestamp, source handles, claims, and staleness
  policy.

Next action:

- Add a `repo_wiki` connector envelope to the admin demo connector catalog so
  DeepWiki-like tools can be represented as governed source adapters without
  exposing raw repo scans by default.

## 2026-06-01 Repo Wiki Connector Envelope

- Added `repo-wiki` to the admin demo connector catalog.
  - `source_system: repo_wiki`
  - default target: `repowiki://local/baltor-admin-demo?ref=main`
  - object types: `repo_wiki_page`, `architecture_diagram`, `source_link`,
    `repo_summary`, and `code_context_claim`
  - sync triggers: `post_commit_hook`, `push_webhook`,
    `merge_request_webhook`, `pipeline_artifact`, `file_watcher`, and
    `scheduled_poll`
  - raw source access remains fallback only.
  - generated repo documentation is marked as derived context, not source truth.
- Updated the end-to-end proof to assert the connector catalog includes
  `repo_wiki`, its safety/retrieval policy, and the core event triggers needed
  for commits, pushes, and pipeline artifacts.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Latest proof:

- run ID: `adm-792f750b3d`
- connector-envelope proof run: `adm-0ef3202910`
- context gateway result: `ctxr-adm-792f750b3d`
- connector count from MCP self-test: 9
- queue trend: `shrinking`
- queue-health warnings: 1 stale-pending backlog warning from the shared queue.

## 2026-06-01 Context Object Records Export

- Added `context_object_graph_records()` to the admin demo server.
  - Projects an existing run into standardized record families:
    `baltor.context-object.v1`, `baltor.context-version.v1`,
    `baltor.context-artifact.v1`, `baltor.context-relationship.v1`,
    `baltor.context-event.v1`, and `baltor.context-pack.v1`.
  - Source records, connector envelopes, claims, RAG records, graph nodes,
    graph edges, and context packs are converted into source-linked, policy
    carrying, versioned records.
  - Relationships map graph edge labels into controlled relationship types,
    including `MAY_SUPERSEDE` for dated ownership conflicts.
- Added `context-objects` as an export kind.
  - Package type: `baltor.context-objects.v1`.
  - Internal record envelope kind:
    `baltor.context-object-graph-records.v1`.
  - Download page now includes a context objects export button.
- Updated end-to-end proof assertions.
  - Requires context objects, versions, artifacts, relationships, events, and
    one context pack projection.
  - Requires immutable-version policy and `MAY_SUPERSEDE` relationship proof.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Latest proof:

- run ID: `adm-8357098fd0`
- connector-envelope proof run: `adm-b5d6091012`
- context gateway result: `ctxr-adm-8357098fd0`
- exports include `context-objects`
- context cache manifest kind:
  `baltor.local-context-cache-manifest.v1`
- MCP self-test passed with `search_result_id: ctxr-adm-8357098fd0`
- queue trend: `growing` during the latest proof window
- queue-health warnings: 1 stale-pending backlog warning from the shared queue.

## 2026-06-01 Context Fabric Product Surface

- Added `docs/architecture/baltor-context-fabric-product-blueprint.md`.
  - Stores the integrated product vision: Context Fabric as a governed
    context-object platform, not a chatbot or vector DB wrapper.
  - Defines product planes, modules, packaging, deployment models, standards
    mappings, MVP phases, and invariants.
- Added product-level schemas:
  - `schemas/context-provider.schema.json`
  - `schemas/context-pack-builder.schema.json`
  - `schemas/context-product-surface.schema.json`
- Expanded `/api/context-gateway/context-schema-catalog`.
  - Now includes provider, pack-builder, and product-surface schema kinds.
- Added `/api/context-gateway/product-surface`.
  - Returns `baltor.context-product-surface.v1`.
  - Exposes modules, interfaces, deployment models, standards mappings, MVP
    phases, and invariants.
- Added `context_product_surface` to the MCP wrapper and self-test.
- Updated the end-to-end proof to assert product surface, MCP interface,
  Atlassian/Rovo deployment model, and durable source-handle invariant.

Validation:

```bash
python3 -m json.tool schemas/context-provider.schema.json
python3 -m json.tool schemas/context-pack-builder.schema.json
python3 -m json.tool schemas/context-product-surface.schema.json
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Latest proof:

- run ID: `adm-73cc9ff264`
- connector-envelope proof run: `adm-ee7cc909cf`
- context gateway result: `ctxr-adm-73cc9ff264`
- product route included in route proof:
  `/api/context-gateway/product-surface`
- schema catalog count from MCP self-test: 9
- product surface kind from MCP self-test:
  `baltor.context-product-surface.v1`
- product module count from MCP self-test: 14
- MCP tools include `context_product_surface`
- queue trend: `shrinking`
- queue-health warnings: 1 stale-pending backlog warning from the shared queue.

Follow-up:

- Added `sync_policy` to connector envelopes.
- `repo_wiki` now advertises event-driven triggers:
  `post_commit_hook`, `push_webhook`, `merge_request_webhook`,
  `pipeline_artifact`, `file_watcher`, and `scheduled_poll`.
- The end-to-end proof now asserts the core repo-wiki triggers for commits,
  pushes, and pipeline artifacts, and confirms commit-scoped outputs are
  required.

Next action:

- Add a repo-wiki import mock/export shape such as
  `baltor.repo-wiki-page.v1` so generated wiki pages can be represented in
  context packs with commit-scoped source handles before wiring a real
  DeepWiki/OpenDeepWiki/RepoWiki backend.

## 2026-06-01 Source-Aware Reranking and LoRA Rerankers

- Added reranking as a separate Context Fabric surface from model routing.
  - Model routing chooses the worker/reviewer tier.
  - Reranking chooses which retrieved candidates enter a context pack and in
    what order.
- Added `docs/architecture/baltor-reranking-and-lora-rerankers.md`.
  - Defines the deterministic -> lexical -> vector -> cross-encoder ->
    LoRA/domain -> LLM judge -> human review reranking ladder.
  - Documents that LoRA/domain rerankers are eval-gated adapter profiles with
    lineage and source handles, not global source-of-truth rules.
- Added `schemas/context-reranker-profile.schema.json`.
  - Defines `baltor.context-reranker-profile.v1`.
  - Captures stage, slot, examples, deployment modes, candidate-pool limits,
    latency profile, training metadata, and policy.
- Added `schemas/context-reranking-policy.schema.json`.
  - Defines `baltor.context-reranking-policy.v1`.
  - Captures source-aware scoring signals, pipeline stages, escalation
    triggers, and LoRA adapter promotion policy.
- Added `/api/context-gateway/reranking`.
  - Returns `baltor.context-reranking.v1`.
  - Exposes seven reranker profiles, the source-aware policy, and a sample
    rerank decision.
- Added MCP tool `context_reranking`.
- Added Postgres persistence tables for `context_reranker_profile` and
  `context_reranking_policy`.
- Updated the product-surface, schema-catalog, current-state, and proof scripts
  so reranking is part of the active API/MCP contract.

Validation:

```bash
python3 -m json.tool schemas/context-reranker-profile.schema.json
python3 -m json.tool schemas/context-reranking-policy.schema.json
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

DDL proof:

```bash
sg docker -c "docker run --rm --name baltor-schema-proof-rerank -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=baltor_schema_proof -p 55433:5432 -v /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing/db/postgres/schema.sql:/schema.sql:ro -d pgvector/pgvector:pg16"
sg docker -c "docker exec baltor-schema-proof-rerank pg_isready -U postgres -d baltor_schema_proof"
sg docker -c "docker exec baltor-schema-proof-rerank psql -U postgres -d baltor_schema_proof -v ON_ERROR_STOP=1 -f /schema.sql"
sg docker -c "docker exec baltor-schema-proof-rerank psql -U postgres -d baltor_schema_proof -At -c \"select table_name from information_schema.tables where table_schema='public' and table_name in ('context_reranker_profile','context_reranking_policy','context_model_profile','context_model_routing_policy') order by table_name;\""
sg docker -c "docker stop baltor-schema-proof-rerank"
```

Latest proof:

- run ID: `adm-3ec53fd89f`
- connector-envelope proof run: `adm-ccfcc6d14e`
- context gateway result: `ctxr-adm-3ec53fd89f`
- reranking route included in route proof:
  `/api/context-gateway/reranking`
- schema catalog count from MCP self-test: 16
- MCP reranker profile count: 7
- MCP sample recommended stage:
  `cross_encoder_then_lora_if_domain_adapter_available`
- MCP tools include `context_reranking`
- queue-health warnings: 0
- queue trend: `flat` with no stale pending or active worker jobs in the proof
  sample.

## 2026-06-01 Provider-Neutral Model Routing Ladder

- Added provider-neutral model routing as a first-class Context Fabric surface.
  - Model families such as MiniMax, Kimi, DeepSeek, Mistral, Llama, Qwen,
    Gemma, GLM, Nemotron, Granite, and Jamba are represented as examples in
    capability slots, not as routing rules.
  - Routing is driven by task type, cost/privacy constraints, uncertainty,
    conflict, temporal fragility, graph centrality, downstream risk, source
    quality, ambiguity, and model disagreement.
- Added `schemas/context-model-profile.schema.json`.
  - Defines `baltor.context-model-profile.v1`.
  - Captures tier, slot, deployment modes, example model families, default
    tasks, max risk, cost profile, privacy constraints, and policy.
- Added `schemas/context-model-routing-policy.schema.json`.
  - Defines `baltor.context-model-routing-policy.v1`.
  - Captures the weighted escalation formula, threshold ladder, escalation
    triggers, and provider-neutral policy assertions.
- Added `docs/architecture/baltor-model-routing-ladder.md`.
  - Documents the deterministic -> small local -> mid open -> large open ->
    ensemble -> frontier -> human review ladder and the score thresholds.
- Added `/api/context-gateway/model-routing`.
  - Returns `baltor.context-model-routing.v1`.
  - Exposes seven model profiles, the routing policy, and a sample route
    decision for the requested task/risk profile.
- Added MCP tool `context_model_routing`.
- Added Postgres persistence tables for `context_model_profile` and
  `context_model_routing_policy`, keeping per-call decisions in
  `model_route_decision`.
- Updated the product-surface and schema-catalog proofs so provider-neutral
  routing is part of the active API/MCP contract.

Validation:

```bash
python3 -m json.tool schemas/context-model-profile.schema.json
python3 -m json.tool schemas/context-model-routing-policy.schema.json
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

DDL proof:

```bash
sg docker -c "docker run --rm --name baltor-schema-proof -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=baltor_schema_proof -p 55432:5432 -v /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing/db/postgres/schema.sql:/schema.sql:ro -d pgvector/pgvector:pg16"
sg docker -c "docker exec baltor-schema-proof pg_isready -U postgres -d baltor_schema_proof"
sg docker -c "docker exec baltor-schema-proof psql -U postgres -d baltor_schema_proof -v ON_ERROR_STOP=1 -f /schema.sql"
sg docker -c "docker exec baltor-schema-proof psql -U postgres -d baltor_schema_proof -At -c \"select table_name from information_schema.tables where table_schema='public' and table_name in ('context_model_profile','context_model_routing_policy','model_route_decision') order by table_name;\""
sg docker -c "docker stop baltor-schema-proof"
```

Latest proof:

- run ID: `adm-4afc475a12`
- connector-envelope proof run: `adm-d03b200288`
- context gateway result: `ctxr-adm-4afc475a12`
- model-routing route included in route proof:
  `/api/context-gateway/model-routing`
- schema catalog count from MCP self-test: 14
- MCP model profile count: 7
- MCP sample recommended route: `large_open`
- MCP tools include `context_model_routing`
- queue-health warnings: 0
- queue trend: `growing` with no stale pending or active worker jobs in the
  proof sample.

## 2026-06-01 Flexible Facets, Assertions, and Dimensions

- Extended the context-object schema family for flexible, non-fragile context
  documents:
  - `baltor.context-assertion.v1`
  - `baltor.context-dimension-definition.v1`
  - `baltor.context-dimension-value.v1`
- Extended `baltor.context-object.v1` with optional namespaced `facets`,
  `five_w_one_h`, and `dimension_summary` fields.
- Updated the schema catalog to expose 12 schema records.
- Updated the `context-objects` export so every run now materializes:
  - flexible facets on context objects;
  - universal who/what/when/where/why/how projections;
  - source-linked assertions for claims, relationship projections, and 5W1H;
  - first-class dimension definitions for verifiability, authority, freshness,
    operational risk, sensitivity, prompt-injection risk, and actionability;
  - dimension values as versioned assessments rather than source facts.
- Updated the context-object graph profile, current-state notes, and test plan
  to include assertions and dimensions as part of the durable standard.

Validation:

```bash
python3 -m json.tool schemas/context-object.schema.json
python3 -m json.tool schemas/context-dimension-definition.schema.json
python3 -m json.tool schemas/context-dimension-value.schema.json
python3 -m json.tool schemas/context-assertion.schema.json
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Latest proof:

- run ID: `adm-d2e229dadd`
- connector-envelope proof run: `adm-61420124c9`
- context gateway result: `ctxr-adm-d2e229dadd`
- context schema catalog count: 12
- context-object export counts:
  - objects: 72
  - versions: 72
  - artifacts: 40
  - relationships: 58
  - assertions: 149
  - dimension definitions: 7
  - dimension values: 437
  - events: 73
  - packs: 1
- queue trend: `shrinking`
- queue-health warnings: 0

Next action:

- Add a first-class `context_dimensions` gateway/MCP tool so clients can query
  the dimension registry and object assessments without downloading the full
  `context-objects` export.

## 2026-06-01 Context Dimensions Gateway Tool

- Added `/api/context-gateway/dimensions`.
  - Returns `baltor.context-dimensions.v1`.
  - Supports `run_id`, `dimension_id`, `subject_id`, and `max_values`.
  - Returns empty but valid contract metadata when no run exists, so initial
    route readiness checks remain stable.
  - Enforces a bounded response policy and labels scores as assessments rather
    than source facts.
- Added `context_dimensions` to the local MCP wrapper and self-test.
- Updated the end-to-end proof to include the dimensions route and to assert
  filtered verifiability definitions/values.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Latest proof:

- run ID: `adm-f74c11a5c8`
- connector-envelope proof run: `adm-a282561fd3`
- context gateway result: `ctxr-adm-f74c11a5c8`
- dimensions route included in route proof:
  `/api/context-gateway/dimensions`
- MCP self-test:
  - `dimensions_kind: baltor.context-dimensions.v1`
  - `dimension_definition_count: 1`
  - `dimension_value_count: 5`
  - tools include `context_dimensions`
- queue trend: `flat`
- queue-health warnings: 0

Next action:

- Add a small UI panel on `/admin-demo/explore` or `/admin-dashboard/monitor`
  that surfaces top dimensions and high-risk/low-verifiability objects from
  the latest run.

## 2026-06-01 Dimension Engine UI Panel

- Added a Dimension engine panel to `/admin-demo/explore`.
  - Shows total dimension definitions, dimension values, and assertions.
  - Ranks highest operational-risk context objects.
  - Ranks lowest verifiability context objects.
- Added a compact Dimension engine panel to `/admin-dashboard/monitor`.
- Updated the end-to-end proof so post-run UI checks assert:
  - `Dimension engine`
  - `Highest operational risk`
  - `Lowest verifiability`

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Latest proof:

- run ID: `adm-4c5ea8f4a8`
- connector-envelope proof run: `adm-7d937c03e5`
- context gateway result: `ctxr-adm-4c5ea8f4a8`
- dimensions route included in route proof:
  `/api/context-gateway/dimensions`
- UI dimension assertions passed for:
  - `/admin-demo/explore?run=adm-4c5ea8f4a8`
  - `/admin-dashboard/monitor?run=adm-4c5ea8f4a8`
- MCP self-test:
  - `dimensions_kind: baltor.context-dimensions.v1`
  - `dimension_definition_count: 1`
  - `dimension_value_count: 5`
  - tools include `context_dimensions`
- queue trend: `growing`
- queue-health warnings: 1 stale-pending backlog warning from the shared queue.

Next action:

- Add persistence DDL for assertions, dimensions, and flexible JSONB facets in
  `db/postgres/schema.sql`, with GIN and dimension/risk indexes.

## 2026-06-01 Context Object Fabric Postgres DDL

- Added a Context Object Fabric persistence block to
  `db/postgres/schema.sql`.
- New tables:
  - `context_object`
  - `context_version`
  - `context_relationship`
  - `context_assertion`
  - `context_dimension_definition`
  - `context_dimension_value`
  - `context_artifact`
  - `context_lineage_event`
  - `context_pack`
- Added indexes for:
  - object tenant/type/source/ACL lookup;
  - JSONB facets, 5W1H projections, and document bodies;
  - relationship from/to/type traversal and hyperedge endpoints;
  - assertion subject/predicate and JSONB values;
  - dimension subject, dimension ID, normalized score, label, scope, and
    assessed time;
  - artifact full-text and derived-from lookup;
  - lineage inputs/outputs and pack source handles.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
```

DDL validation:

```bash
sg docker -c "docker run --rm --name baltor-schema-proof -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=baltor_schema_proof -p 55432:5432 -v /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing/db/postgres/schema.sql:/schema.sql:ro -d pgvector/pgvector:pg16"
sg docker -c "docker exec baltor-schema-proof pg_isready -U postgres -d baltor_schema_proof"
sg docker -c "docker exec baltor-schema-proof psql -U postgres -d baltor_schema_proof -v ON_ERROR_STOP=1 -f /schema.sql"
sg docker -c "docker exec baltor-schema-proof psql -U postgres -d baltor_schema_proof -At -c \"select table_name from information_schema.tables where table_schema='public' and table_name like 'context_%' order by table_name;\""
sg docker -c "docker exec baltor-schema-proof psql -U postgres -d baltor_schema_proof -At -c \"select indexname from pg_indexes where schemaname='public' and tablename in ('context_object','context_relationship','context_assertion','context_dimension_value','context_pack') order by indexname;\""
sg docker -c "docker stop baltor-schema-proof"
```

DDL proof result:

- `/schema.sql` executed successfully with `ON_ERROR_STOP=1`.
- Context tables created:
  - `context_artifact`
  - `context_assertion`
  - `context_dimension_definition`
  - `context_dimension_value`
  - `context_lineage_event`
  - `context_object`
  - `context_pack`
  - `context_relationship`
  - `context_version`
- Verified indexes include:
  - `context_object_facets_gin_idx`
  - `context_object_5w1h_gin_idx`
  - `context_relationship_endpoints_gin_idx`
  - `context_assertion_value_gin_idx`
  - `context_dimension_value_dimension_idx`
  - `context_dimension_value_scope_gin_idx`
  - `context_pack_source_handles_gin_idx`

Next action:

- Add a lightweight migration/export mapper that converts
  `context_object_graph_records(run)` into insertable rows for the new
  Postgres tables, while keeping raw source dumps out of relational rows.

## 2026-06-01 Context Object Graph Profile Implementation

- Stored the broader context object fabric design in
  `docs/architecture/baltor-context-object-graph-profile.md`.
  - Covers stable objects, immutable versions, derived artifacts, typed
    relationships, append-only lineage/history events, context packs,
    lifecycle stages, policy inheritance, retrieval projections, and deployment
    variants.
- Expanded `schemas/context-object.schema.json`.
  - Added `current_version_id`, source/native IDs, source URL, ACL ID,
    classification, and broader cross-industry object types.
- Added graph-profile schema family:
  - `schemas/context-version.schema.json`
  - `schemas/context-artifact.schema.json`
  - `schemas/context-relationship.schema.json`
  - `schemas/context-event.schema.json`
  - `schemas/context-pack.schema.json`
- Added `/api/context-gateway/context-schema-catalog`.
  - Returns `baltor.context-schema-catalog.v1`.
  - Lists the context graph schema family and contract layers.
- Added `context_schema_catalog` to the MCP wrapper and self-test.
- Updated the end-to-end proof to assert the schema catalog includes object,
  version, artifact, relationship, event, and pack kinds.

Validation:

```bash
python3 -m json.tool schemas/context-object.schema.json
python3 -m json.tool schemas/context-version.schema.json
python3 -m json.tool schemas/context-artifact.schema.json
python3 -m json.tool schemas/context-relationship.schema.json
python3 -m json.tool schemas/context-event.schema.json
python3 -m json.tool schemas/context-pack.schema.json
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Latest proof:

- run ID: `adm-c54fb4953a`
- connector-envelope proof run: `adm-4e169c4b14`
- context gateway result: `ctxr-adm-c54fb4953a`
- schema catalog route included in route proof:
  `/api/context-gateway/context-schema-catalog`
- schema catalog kind: `baltor.context-schema-catalog.v1`
- schema count from MCP self-test: 6
- MCP tools include `context_schema_catalog`
- queue trend: `shrinking`
- queue-health warnings: 1 stale-pending backlog warning from the shared queue.

## 2026-06-01 Context Object Standards Profile

- Added `docs/architecture/baltor-context-object-standards.md`.
  - Clarifies that there is no single universal LLM context-object standard.
  - Separates runtime invocation context, agent state, durable context objects,
    and request-scoped context packs.
  - Maps Baltor context objects onto existing standards: MCP, LangChain-style
    `contextSchema`, JSON Schema, JSON-LD/schema.org, W3C PROV, W3C Web
    Annotation, RO-Crate, SPDX/CycloneDX, OpenLineage, and OpenTelemetry.
- Added `schemas/context-object.schema.json`.
  - Defines `baltor.context-object.v1`.
  - Requires `ctx://` source handles and policy fields for derived context,
    promotion, and raw-source-dump handling.
  - Includes provenance, evidence selectors, lineage, MCP delivery metadata,
    freshness, and policy controls.
- Added `/api/context-gateway/context-object-schema`.
  - Returns `baltor.context-object-schema.v1`.
  - Exposes the raw JSON Schema plus a compact standards profile and policy
    summary for clients.
- Added `context_object_schema` to the MCP wrapper and self-test.
- Updated the end-to-end proof to assert the schema endpoint, durable context
  kind, `ctx://` handle pattern, and policy summary.

Validation:

```bash
python3 -m json.tool schemas/context-object.schema.json
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Latest proof:

- run ID: `adm-9b87821bfe`
- connector-envelope proof run: `adm-abf78fecd5`
- context gateway result: `ctxr-adm-9b87821bfe`
- context cache manifest kind:
  `baltor.local-context-cache-manifest.v1`
- schema route included in route proof:
  `/api/context-gateway/context-object-schema`
- MCP self-test:
  `context_object_kind: baltor.context-object.v1`
- MCP tools include `context_object_schema`
- queue trend: `shrinking`
- queue-health warnings: 1 stale-pending backlog warning from the shared queue.

## 2026-06-01 Event-Driven Sync Contracts

- Added `docs/architecture/baltor-event-driven-context-sync.md`.
  - Covers push, pull, and push-then-pull sync modes.
  - Defines normalized sync events, check gates, worker routing, and
    `baltor.repo-wiki-artifact-manifest.v1`.
  - Maps GitHub/GitLab events, CI artifacts, Tekton, Argo Events, local hooks,
    file watchers, and scheduled polling into Baltor lanes.
- Added `/api/context-gateway/sync-contracts`.
  - Returns `baltor.context-sync-contracts.v1`.
  - Exposes trigger types, check gates, artifact manifest kinds, worker routing,
    and connector summaries.
- Added `context_sync_contracts` to the local MCP wrapper and self-test.
- Updated the test plan and goal prompt so the sync architecture is part of the
  active read-first set.

Validation:

```bash
python3 -m py_compile scripts/baltor_admin_demo_server.py scripts/test_baltor_admin_demo_flow.py scripts/baltor_context_gateway_mcp.py
python3 scripts/test_baltor_admin_demo_flow.py --base-url http://127.0.0.1:9304
python3 scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304 --self-test
```

Latest proof:

- run ID: `adm-4f92a59602`
- connector-envelope proof run: `adm-6eac40e3bc`
- context gateway result: `ctxr-adm-4f92a59602`
- sync route included in route proof:
  `/api/context-gateway/sync-contracts`
- MCP self-test:
  `sync_contract_kind: baltor.context-sync-contracts.v1`
- sync trigger count: 9
- queue trend: `shrinking`
- queue-health warnings: 1 stale-pending backlog warning from the shared queue.

Next action:

- Add a repo-wiki import mock/export shape such as
  `baltor.repo-wiki-page.v1` so generated wiki pages can be represented in
  context packs with commit-scoped source handles before wiring a real
  DeepWiki/OpenDeepWiki/RepoWiki backend.
