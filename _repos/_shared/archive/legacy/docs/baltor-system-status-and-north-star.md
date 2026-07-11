# Baltor — system status + north star (2026-06-04)

## North star (UPDATED per owner)
From "a demo of the context engine" → **a fully functional system: every component and module
connected end-to-end, with a realtime operations dashboard that shows things firing live.** The
prettiness of the static demo is not the goal; the goal is a running system whose real activity you
can watch.

## Verified system status (measured, not claimed — 2026-06-04, Python 3.14.4)
- **Parse:** 376/376 Python modules compile (0 syntax failures).
- **Unit self-tests:** 162/162 pass when run correctly (`PYTHONPATH=<repo>`, excluding `.pyc`). The
  flywheel watchdog covers 34 of these continuously (`scripts/baltor_flywheel.py --once`).
- **Live API server (`scripts/baltor_admin_demo_server.py`):** WAS broken on Python 3.13+
  (`import cgi`, removed by PEP 594) — **fixed** with a stdlib `email`-based multipart parser
  (`parse_multipart_form`). Now imports cleanly; every `/api/*` route returns 200 over live HTTP;
  the heartbeat queue contract is stable with or without Redis.
- **End-to-end API flow test (`scripts/test_baltor_admin_demo_flow.py`): PASS** (exit 0) — upload
  (multipart) → background-thread processing → claim/term-clarity extraction → exports → heartbeat,
  against a live Redis on :6379.
- **Static demo console (`web/baltor/demo-console.html`):** verified in real Chrome (15/15
  assertions) — but it is a **deterministic replay** of pre-baked JSON, NOT live system activity.

## Dependency reality (this host)
- Python **3.14.4**, **no pip/ensurepip** (stripped). Pure-Python deps must be vendored onto
  `PYTHONPATH` (e.g. `redis` 8.0 vendored to `/tmp/baltor-vendor` for the flow test). **Redis is
  optional** — run processing uses an in-process daemon thread; the queue/worker path is the
  Redis-backed extra. **Docker is available** but real containers are out of scope for the demo.
- Implication: the realtime dashboard must work **offline, no Redis, no pip** — the admin server's
  event stream is in-process, so this is achievable.

## What's connected vs. what's a seam (the integration gap to close)
| Piece | State |
|---|---|
| Admin API server + `/api/admin-dashboard/events` live stream + heartbeat | REAL, running, fixed |
| `log_event(...)` in-process event bus (admin server) | REAL — but only the admin upload flow emits to it |
| context-engine modules: context_graph / context_compress / context_swarm / source_expansion / verified_context_flow / ingest connectors | REAL + self-tested — but they DON'T emit lifecycle events to the live bus |
| Static demo console (animated replay) | REAL but offline replay, not live |
| Realtime dashboard fed by actual component firings | **MISSING — the work** |

## The work (new primary tracks — supersede the "five tracks complete" framing)
1. **Unified event bus** — one in-process (and optionally Redis/stream-backed) event channel that
   EVERY component emits lifecycle events to (`component.started/progressed/finished`, contradiction
   found, swarm finding, review routed, pack built, receipt issued), with correlation ids.
2. **Connect all modules to it** — graph interrogation, compression, swarm, expansion, ingest,
   verified_context_flow each emit real events as they run (start from the modules already shipped).
3. **Realtime ops dashboard** — extend the admin dashboard (`/admin-demo/` already polls
   `/api/admin-dashboard/events`) into a live view that shows components firing as a run flows
   through the pipeline — replacing the static replay with the real stream (degrade to replay only
   when nothing is running).
4. **End-to-end integration tests** (not just unit self-tests) — run the whole system on a fixture
   and assert the expected sequence of events fired; add to the proof suite.
5. **Make the live backend a first-class, documented, one-command launch** (server + optional vendored
   redis), wired to the same demo data the console uses.

## Non-negotiables (unchanged)
Proof-per-increment (offline deterministic self-tests in `PROOF_MODULES`); real-or-labeled-SEAM;
no-magic-values; verify-first; no canonical mutation; synthetic data only; no commits without ask.

## Canonical goal command + tech decisions (2026-06-04, owner directive v2)
The canonical driver is now **`/baltor-connected-system-goal`** (`.claude/commands/baltor-connected-system-goal.md`).
It supersedes `baltor-full-app-goal` as the loop target (same north star, more concrete). Forcing
function: open `/dashboard`, click **Run Full Pipeline**, watch the whole system fire live — if a
module doesn't emit an event, it isn't connected.

Tech decisions (owner-provided, verified):
- **Realtime transport: SSE first** (`GET /api/events/stream` + browser `EventSource`) — simple,
  one-way, native; WebSockets only later if bidirectional controls are needed.
- **Events are OTel-shaped** (trace/correlation/causation ids) so they can later feed an OTel collector.
- **Durable execution later**: Temporal/DBOS/Restate behind the worker seam (NOT now); **KEDA** for
  K8s event-scaling later. All are swaps behind the existing seams, not the demo path.
- **Connect, don't recreate**: extend `scripts/baltor_admin_demo_server.py` (the SSE host + existing
  `/api/admin-dashboard/events` + `log_event`) and `scripts/context_events.py` (the in-process bus);
  do not scaffold a parallel `apps/`+`packages/` tree.

### MVP vertical slice (build first)
EventBus → wire the shipped engines (context_graph/compress/swarm/source_expansion) + the pipeline to
emit → SSE route → `web/baltor/dashboard.html` consuming it → `POST /api/demo/run-full-pipeline`
firing the full sequence → all visible live. Offline integration self-test asserts the event sequence.
