---
description: Build a FULLY CONNECTED, runnable Baltor system — every existing module emits events onto one bus, a realtime /dashboard shows them fire live, and one pipeline call walks the whole motion. Connect what exists; do NOT rebuild or scaffold a parallel app.
---

You are Claude Code, a long-running implementation agent for the **Baltor Context Engine** repo.
Mission: a **fully connected, runnable local system** where frontend, backend, the shipped engines,
events, packs, receipts, review, evals, and swarm are WIRED TOGETHER and visible firing live on a
realtime dashboard. **The forcing function: a user opens `/dashboard`, clicks "Run Full Pipeline",
and watches the whole system fire in real time. If a module doesn't emit an event, it isn't
connected.** Do not stop after planning. Do not only write docs. Ship a thin working vertical slice,
PROVE it with an offline self-test, record a receipt, continue.

## ⚠️ THIS REPO IS NOT GREENFIELD — CONNECT, don't recreate (read first, every pass)
Read `docs/baltor-system-status-and-north-star.md` (verified status) before building. Anchor map —
EXTEND these; creating a parallel `apps/`+`packages/` tree or a second event bus is a DEFECT:

| Generic concept in the spec | The REAL thing in this repo (extend it) |
|---|---|
| Backend API + SSE host | `scripts/baltor_admin_demo_server.py` (stdlib http.server; FIXED cgi→email). Already serves `/api/admin-dashboard/events`, `/api/admin-dashboard/status`, `/api/debug/heartbeat`, `/admin-demo/`, `/api/context-gateway/*`. ADD `GET /api/events/stream` (SSE) + the new demo/graph/swarm/eval routes HERE. |
| EventBus | `scripts/context_events.py` (in-process pub/sub, monotonic `seq`, single `EVENT_KINDS`) + the server's existing `log_event(...)`. Make them ONE bus; do not invent a third. |
| Event types | the `EVENT_KINDS` enum in `scripts/context_events.py` is the single source — extend it, mirror into `schemas/events/*`. |
| Demo dataset | ALREADY EXISTS: `demo-data/acme-billing/` (BILL-782, ADR-014 [max_retries=5], stale runbook [3], retry.py, test, INC, openapi, OWNERS) + `demo-data/cfpb-sample/`. Do NOT regenerate or change the planted facts. |
| Context object / graph / source handles | `scripts/context_graph.py` (+ `demo-data/*/seed-graph.json`), `schemas/context-object|relationship|assertion`, `scripts/source_handle_resolver.py` + `scripts/source_expansion.py`. |
| Pack builder / compression | `scripts/context_compress.py` (deterministic ladder) + `scripts/demo_full_app.py` (builds pack+lineage+receipt). |
| Swarm | `scripts/context_swarm.py` + `schemas/swarm/*`. Review: `schemas/governance/steward-review-*`. Evals: `scripts/eval/context_lift_matrix.py` + `measured_lift_headtohead.py`. |
| Frontend | `_repos/baltor/frontend/` (SPA shell `index.html`+`app.js`; static `demo-console.html`, `reviews.html`). ADD a live `dashboard.html`; extend `app.js` nav. Do NOT build `apps/web`. |
| Run state | `.baltor-demo/state/*.jsonl|json` is fine for the demo; the admin server already holds in-memory run + event state. |

## Verified facts to honor (this host)
Python **3.14, NO pip/ensurepip** → vendor pure-Python deps to `/tmp/baltor-vendor` (e.g. `redis`),
never `pip install`. **Redis OPTIONAL** (runs process via an in-process daemon thread; the event
stream is in-process) → the dashboard MUST work offline/no-pip/no-Redis. The admin server flow test
passes (`scripts/test_baltor_admin_demo_flow.py`). Brands LOCKED; retire user-facing "Oracle".

## Realtime dashboard (the forcing function) — `_repos/baltor/frontend/dashboard.html` + server routes
Live view (SSE-first: `GET /api/events/stream` via `EventSource`; poll `GET /api/events` as
fallback). Panels: (1) live event stream (seq, kind, stage, module, object_ref, status, severity,
correlation_id, receipt/pack/review/eval/swarm refs); (2) six-stage board (Source→Reconciliation→
Anti-Fragility→Enhancement→Optimization→Consumption + Verification rail) lighting up as events fire;
(3) worker/module activity; (4) queue/job panel; (5) graph summary (nodes/edges/claims/handles/
packs/receipts); (6) recent artifacts (latest pack/receipt/review/swarm consensus/eval); (7) controls:
Seed · Run Full Pipeline · context_for_ticket(BILL-782) · Interrogate graph · Swarm object · Run lift
eval · Clear log · Reset. Keep the dark/compact aesthetic; no Oracle copy.

## The pipeline (the headline) — `POST /api/demo/run-full-pipeline`
Emits, in order, each visible on `/dashboard`, composing the EXISTING engines:
`pipeline.started` → seed/load `demo-data/acme-billing` → `source.received`/`source_handle.created`
(source_handle_resolver) → `context_object.created` (seed-graph) → `relationship.created` →
`reconciliation.*` + `contradiction_found` (context_graph.find_contradictions: runbook 3 vs ADR 5) →
`rot.detected` (context_rot: runbook stale) → `enhancement.*` → `verification.*` → `review.requested`
(steward-review for the contradiction) → `optimization.*`/`context_pack.created` (context_compress) →
`receipt_issued` (demo_full_app) → `eval.*`/`context_lift.calculated` (context_lift_matrix, mock model)
→ `swarm.*`/`swarm.consensus.created` (context_swarm on obj-runbook) → `pipeline.completed`.

## Pages + routes (extend the admin server + _repos/baltor/frontend)
Pages: `/dashboard` (live) · extend existing `demo-console.html`, `reviews.html` · add `/graph`,
`/objects`, `/objects/:id`, `/packs/:id`, `/receipts/:id`, `/evals`, `/tools`, `/lineage/:id` as
they become backed by real routes (don't ship dead links — `check_demo_console_links.py` guards this).
Routes (add to the admin server): `/api/events`, `/api/events/stream` (SSE), `/api/events/clear`,
`/api/demo/{seed,reset,run-full-pipeline,state}`, `/api/graph*`, `/api/context/objects*`,
`/api/context/for-ticket`, `/api/context/packs*`, `/api/context/receipts/:id`,
`/api/context/source-handles/:id/expand` (source_expansion gate), `/api/reviews*`, `/api/evals*`,
`/api/tools`, `/api/versions*`. Stub-with-real-data is OK; faking is not.

## Model + compression (free/local, offline-first)
LLM is a SEAM via `scripts/model_gateway.resolve_model_route` (deterministic mock default; Ollama/
OpenRouter/Groq optional via env). Deterministic compression FIRST (`context_compress`); LLM only as
a recorded escalation. The whole demo must run with NO model and NO Redis.

## Discipline (non-negotiable, every pass)
Proof-per-increment: every new module ships an offline deterministic `--self-test`, added to
`scripts/baltor_flywheel.py` PROOF_MODULES; `flywheel --once` stays GREEN. Real-or-labeled-SEAM (no
faked events/results). No-magic-values (one EVENT_KINDS source; counts computed). Verify-first; do
NOT reintroduce flagged tools (Kuzu archived → Graphiti; Synapse AI; Microsoft Conductor → DBOS/
Temporal). Determinism in emitted events: use the monotonic `seq`, NOT wall-clock. No canonical
mutation (swarm/proposals are not auto-applied). Working tree only — no commits/push, no pip, no real
containers, no cloud. Durable engine (DBOS/Temporal), KEDA, SSE→WebSockets, OTel collector are LATER
swaps behind the seam, not now.

## MVP vertical slice (build this first; it proves the whole motion)
EventBus (`context_events.py`) → wire `context_graph.interrogate` + `context_compress` + `context_swarm`
+ `source_expansion` + the demo pipeline to emit → SSE route on the admin server → `dashboard.html`
consuming it → `POST /api/demo/run-full-pipeline` firing the full sequence → all visible live. THEN
broaden routes/pages. An offline integration self-test asserts the expected event sequence fired.

## Execution order each pass
1) `flywheel --once` green-check. 2) ORIENT on the anchor map + status doc. 3) pick the highest-leverage
slice toward "watch it fire live". 4) implement by CONNECTING existing modules + emitting events.
5) PROVE (offline self-test + flywheel green). 6) RECORD a receipt to `.agent/baltor-goal-loop-log.md`;
refresh `.agent/baltor-connected-system-final-report.md` every ~5 passes. 7) continue.

## Track B (QUEUED research/prototype — behind the connect-the-engines priority): Vibe Graphing / Workflow Design Lab
VERIFIED real (see `docs/research/masfactory.md`): MASFactory (github.com/BUPT-GAMMA/MASFactory,
arXiv 2603.06007, ACL-2026 demo) — natural-language → editable workflow graph → executable, with a
visualizer + ContextBlock. **Authoring/prototyping layer ONLY — NOT the canonical runtime, durable
engine, policy authority, or context store.** Integration is clean because the substrate is shipped:
MASFactory node/edge hooks → `scripts/context_events.EventBus` → `/api/events/stream` → `/dashboard`;
ContextBlock ← a Baltor pack wrapped with source_handles+receipt+policy. First bakeoff = a graph for
`context_object_swarm` (we already have the agents in `scripts/context_swarm.py`). Pass/fail criteria
+ the dependency caveat (Python 3.14 no-pip → vendor or keep as docs+adapter-stub with the exact
install next-command) are in the research doc. Do NOT scaffold a parallel packages/ tree or 8 schemas
up front; start with the verified doc (done) → one workflow-intent fixture → a runnable POC behind a
seam → then schemas as they're earned by a running graph. Build only AFTER the live dashboard +
engine-emit wiring are solid, OR when the owner explicitly prioritizes the bakeoff.

## Acceptance (the run is "connected" when)
`run-full-pipeline` fires ≥15 distinct event kinds, all visible on `/dashboard` live (SSE) or polled;
context objects + handles from `demo-data`; graph + interrogation; pack + receipt for BILL-782; a
review request for the planted contradiction; a swarm consensus; a mock-model lift eval; version
records; tool registry; NO Oracle copy; offline/no-Redis/no-pip; flywheel GREEN; final report written.
