# P1 — Baltor Context Gateway Hardening

**Warrant:** `docs/architecture/capability-rubric-and-deep-dive-2026-06-11.md` (code-verified deep dive).
That review graded the Baltor context gateway **"MVP skeleton of THE product"** and named five concrete
defects (ctx:// handles die on restart + RUNS never pruned; no receipt on search/fetch; hardcoded CFPB db
path outside the volume; unauthenticated content GETs; admin-demo double-processing). This pass closes all
five **surgically inside the single owned file** `scripts/baltor_admin_demo_server.py` (no other file
touched; the file backs a live `:9301` demo, which was NOT disturbed — every test ran on temp ports + temp
`BALTOR_DURABLE_DB`).

Laws honored: **no-magic-values** (every cap/path is one named, env-overridable constant), **lossless**
(the in-memory `RUNS` dict stays authoritative; durable tables + receipts are an additive derived layer;
nothing is overwritten or dropped), **honest** (degrade-and-record everywhere; `RUN_STORE=None` ⇒
byte-identical prior behavior), **change-verification** (warrant = the deep-dive finding, cited per item).

Net: **+367 / −7** lines, one file. Admin server is allowlisted in `architecture/monolith_allowlist.json`
(budget 750; debt visible) — `check_monolith_allowlist --self-test` stays green.

---

## The five items

### 1. Persist `RUNS` so ctx:// handles survive restart + bounded memory — DONE
- **Why:** `RUNS` was an in-memory `dict` (line 51), never persisted/pruned → every ctx:// handle died with
  the process and memory grew unbounded.
- **How:** the bus rejects unknown event kinds (`scripts/context_events.EVENT_KINDS`, not in scope), so `RUNS`
  cannot ride the event log — it gets its **own durable table**. A second `sqlite3` connection onto the SAME
  WAL db (`BALTOR_DURABLE_DB`) — proven multi-connection-safe (WAL + `busy_timeout`) and co-resident with
  `DurableStore`'s tables — backs `gateway_runs(run_id PK, created_at, updated_at, body_json)`.
  - `RUN_STORE` init + schema: **695–717**. Cap constant `DURABLE_RUNS_MAX` (default 200, env
    `BALTOR_DURABLE_RUNS_MAX`): **678**.
  - `persist_run()` **718–735** (upsert, best-effort, never breaks a live run), `prune_runs()` **737–755**
    (LRU by `created_at`, trims memory AND table), `rehydrate_runs()` **757–783** (startup reload of newest N).
  - Wired into every `RUNS` write: `update_run` **1910–1919**, `set_stage` **1972–1986**,
    `create_background_run` **1967–1969** (+prune), `build_run` **~2117** (+prune). Startup hook in `main()`:
    **6011**.
- **Lossless:** `RUNS` (memory) remains the working copy; the table is a mirror; pruning keeps the newest N in
  BOTH and deletes nothing answer-critical (old demo runs only).

### 2. Issue a receipt on every gateway search + fetch — DONE
- **Why:** the gateway claims "agents propose, Baltor disposes" but minted no receipt on read — the claim was
  aspirational, not auditable. (A `receipt_issued` bus kind already existed.)
- **How:** `gateway_receipt()` **785–824** mints a `baltor.gateway-receipt.v1` (id, ts, operation, run_id,
  handle/query, ok, **content_hash**, `is_truth:false`, served-under-policy), persists it to a durable
  `gateway_receipts` table, AND publishes the existing `receipt_issued` bus event (which auto-persists via the
  bus→durable subscription). Called at the **payload-function layer** so BOTH GET and POST routes (and any
  internal caller) get receipts for free: search **3667, 3737**; fetch **3748, 3755, 3773, 3792** (every
  return path, incl. not-found). Each response now carries a `receipt` block. New public read
  `GET /api/context-gateway/receipts` **5402–5410** + `latest_gateway_receipts()` **826–841**.
- **honest:** serving a pack is *not* asserting its facts true — `is_truth:false` on the receipt makes that explicit.

### 3. Route the hardcoded CFPB ledger path through the durable volume — DONE
- **Why:** line 5379 hardcoded `<repo>/.agent/cfpb_artifact_graph.db` — OUTSIDE the Fly volume, so it died on
  restart.
- **How:** `CFPB_ARTIFACT_GRAPH_DB` **689–693** = env `BALTOR_CFPB_ARTIFACT_GRAPH_DB`, defaulting into the
  directory of `BALTOR_DURABLE_DB` (the volume) when set, else the legacy `.agent/` path (byte-identical for
  local/tests). Used at **5614** (+ `mkdir -p` parent).
- **Deviation (documented):** the *canonical* home is
  `scripts/_config.ADMIN_DEMO_RUNTIME_SETTINGS` via `_admin_demo_path_setting`. That module is **out of scope**
  for this single-file surgical change ("touch nothing else"), so the path is resolved **in-file** with the
  same `env → default` precedence the settings module uses. Follow-up: lift `CFPB_ARTIFACT_GRAPH_DB` into
  `ADMIN_DEMO_RUNTIME_SETTINGS` as `cfpb_artifact_graph_db` when `_config.py` is in scope (trivial, lossless).

### 4. Auth on the ingested-content GET — DONE (conservative)
- **Why:** all GETs were open, including the gateway read of raw ingested content.
- **How:** the **`/api/context-gateway/fetch`** GET (the one route that returns raw ingested bytes) now calls
  the existing `self._authed(parsed)` and 401s when `OH_SHOWCASE_TOKEN` is set: **5384–5393**. POSTs were
  already gated at `do_POST` top. Deliberately conservative — search / glossary / dimensions / status / the
  receipts read stay OPEN so the public demo still reads; **no generated `web/` page calls
  `/fetch`** (verified), and the dashboard already appends `?token=` + handles 401, so nothing breaks.
  Unset token ⇒ byte-identical to prior (local/self-tests open).
- **Considered, deferred:** gating `GET /api/admin-demo/runs/<id>` (also returns run `text`). Left open to avoid
  risking the live dashboard's run-poller; the deep-dive item targeted "gateway reads of ingested content",
  which `/fetch` is. Revisit with a dashboard-token audit.

### 5. Kill the admin-demo double-processing — DONE
- **Why:** `create_background_run` enqueued to Redis AND started an in-process worker thread; when a container
  worker consumed the queue, both processed the run and `sync_worker_ledger` overwrote the in-process result
  (the race the deep dive found).
- **How:** ONE path. The in-process worker is now the **fallback only** — started solely when the Redis
  enqueue did **not** publish (`if not published:` **1975–1981**); when it published, a `run.delegated` event
  records that the container worker owns it (no double-run, no overwrite race). When there is no Redis (local
  demo / tests), `published` is false → the in-process worker runs exactly as before (byte-identical).

---

## Restart-survival trace (live, temp port 9357, temp db, `OH_SHOWCASE_TOKEN` set; `:9301` untouched)

```
START server #1 (BALTOR_DURABLE_DB=temp, token set)
POST /admin-demo/runs  WITHOUT token => HTTP 401     # POST gated
POST /admin-demo/runs  WITH token    => run created
GET  /context-gateway/search  NO token => HTTP 200   # item4: search stays PUBLIC
HANDLE = ctx://baltor/adm-65891c0b0b/component/file-path=pasted-context-txt/page=1/component-id=component-001
GET  /context-gateway/fetch  NO token   => HTTP 401   # item4: ingested-content fetch GATED
GET  /context-gateway/fetch  WITH token => ok=True receipt=gwr-dc6ee92f8ef0   # item2
GET  /context-gateway/receipts          => durable=True count=3 ops=[context.fetch, context.search]
--- kill -9 server #1 ---
START server #2 on the SAME db (fresh process)
  log: [durable] ctx:// runs rehydrated=1 (cap=200)                            # item1 rehydrate
GET  /context-gateway/fetch (same handle) WITH token => ok=True kind=component receipt=gwr-a1321c0af8f0  # item1 SURVIVES
GET  /context-gateway/receipts                       => count after restart=4  # receipts persisted
server stderr tracebacks: (none)
```

## Test PASS lines

New in-file proof: `python3 scripts/baltor_admin_demo_server.py --self-test` (function `_self_test` **5883**;
spawns the server as a subprocess like `check_durable_restart_survival`, but drives run→search→fetch —
deliberately NOT the broken `/api/demo/run-full-pipeline`). Ran 2× → identical PASS:

```
[ok] item3: CFPB ledger path lands in the durable volume dir
[ok] item1: RUN_STORE initializes when BALTOR_DURABLE_DB is set
[ok] item5: in-process worker is gated behind `if not published:` (no double-run)
[ok] search returns a ctx:// handle + a receipt
[ok] fetch resolves the handle BEFORE restart
[ok] fetch issues a receipt (item 2)
[ok] receipt PERSISTED for fetch + search (durable)
[ok] ctx:// HANDLE SURVIVES RESTART (item 1): same handle still fetches
[ok] post-restart fetch also issues a receipt
[ok] pre-restart receipts persisted across restart
PASS — baltor_admin_demo_server self-test: ctx:// runs + receipts survive a real restart; receipts issued
       on search/fetch; CFPB path honors the volume setting; single (non-double) run engine.
```

Existing checks (each 2×, all exit 0): `check_admin_server`, `check_monolith_allowlist`,
`check_heartbeat_queue_contract`, `check_baltor_guided_demos`, `check_durable_http_enqueue_drain`,
`check_context_response_retrieval_api`, `check_context_object_audit`, `check_contextops_full_stack`,
`check_no_consumption_bypass`, `check_no_api_consumption_bypass`. Full `--self-test` sweep of all
`check_*baltor* / *context* / *gateway*` scripts shows only **pre-existing** failures, **proven not mine**
by reverting the file to HEAD and reproducing them identically:
- `check_inference_gateway`, `check_inference_gateway_redteam`, `check_context_audit_in_pipeline`,
  `check_durable_restart_survival` → all `KeyError: 'node_id'` from `src/teleon/inference/oips.py`
  (`/api/demo/run-full-pipeline` is broken on this branch, unrelated to this file/change).
- `check_baltor_design_system` → a web/ SPA-scope issue, unrelated to this backend change.

---

## Is this the best way? — what would make the gateway the real customer-grade Baltor product

This pass makes the gateway *honest and durable*; it does not yet make it *multi-tenant* or *versioned*. The
critique, deepest-first:

**Tenancy model (the real gap).** Today `RUNS`/`gateway_runs` are global and `latest_run()` is process-wide —
there is no tenant boundary, and the receipts table has no `tenant_id`. The deep-dive's P2 names exactly this
("per-tenant stores"). The right shape: a `tenant_id` column on `gateway_runs`/`gateway_receipts` and a
**per-tenant durable namespace** — there is already a `resolve_isolation(spec, tenant, base_dir, shared_store)`
seam in `do_POST` (used by `/api/dev/isolation`) that yields a per-tenant store + ledger + db path; the gateway
runs should be created/fetched THROUGH that seam, not the global dict. Then `_authed` becomes per-tenant key
auth (the orphaned `/service/*` handshake in `service-auth-and-consumption-model.md` is the Phase-1), and the
content GET gate becomes "this tenant may read this handle" (ACL), not just "a token is present". The current
token gate is a coarse stand-in for that.

**`ctxv://` versioning.** Handles are `ctx://baltor/<run>/<kind>/...` — content-addressable IDs (`ctxv://...@<hash>`)
already exist for context-objects (line ~2349) but the gateway serves and fetches the **mutable** `ctx://` form,
so a fetched handle can silently change underneath an agent. Customer-grade fetch should pin a `ctxv://` (object
id + body hash) and let the receipt's `content_hash` (now recorded) be the verifiable link — i.e. the receipt
should reference the immutable version, and a re-fetch of the same `ctxv://` must be byte-identical or 409. The
hash plumbing I added is the precondition for this; the versioned-fetch route is the next step.

**Receipts schema.** `baltor.gateway-receipt.v1` is intentionally minimal (operation, handle, hash, is_truth,
policy). The deep-dive's P1 backbone wants **one** receipt envelope with **OTel-compatible `trace_id`/`span_id`**
and persistence behind the registered `:9426 local_receipt_service`. Today this is a fourth receipt shape (the
review counts four). The right move is to make `gateway_receipt` emit the shared `ModelInvocationReceipt`-style
envelope (a `gateway` extension) carrying trace correlation, and project it through `:9426` rather than a local
sqlite table — so search/fetch provenance joins the same standardized logging plane as inference receipts.
Until then this table is a correct, durable, but *parochial* receipt store.

**Other:** keyword-only scoring (`keyword_score`) is still the retrieval (vector search `False` in
`gateway_status`); the monolith should split per the allowlist target (`src/baltor/api/...`); and `RUNS`
persistence is a SQLite mirror — the same SQLite→Postgres path the review prescribes for identity/registry
applies here for true scale. None of these block the five fixes; they are the P2 product build.
