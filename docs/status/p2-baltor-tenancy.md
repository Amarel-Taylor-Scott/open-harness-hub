# P2 — Baltor Context Gateway: Tenancy + `ctxv://` Versioned Fetch

**Warrant:** the capability-rubric tenancy-gap finding —
`docs/architecture/capability-rubric-and-deep-dive-2026-06-11.md` grades the gateway "MVP skeleton of THE
product" with "no tenancy/receipts on fetch" (line 25), and lists "tenanted customer-grade context gateway
(ctxv:// fetch, per-tenant stores)" as the P2 product build (line 124). P1
(`docs/status/p1-baltor-gateway-hardening.md`) added durable handles + receipts and ITS OWN critique
(p1 lines 140–168) named exactly these two gaps as the next step. This pass closes both, **surgically
inside the single owned file** `scripts/baltor_admin_demo_server.py` (no other file touched; the file backs
the live `:9301` demo, which was NOT disturbed — every test ran on temp ports + a temp `BALTOR_DURABLE_DB`).

Laws honored: **no-magic-values** (every tenant/version constant is one named, env-overridable definition —
`DEFAULT_TENANT`, `TENANT_HEADER`, `TENANT_PARAM`, `DURABLE_VERSIONS_MAX`); **lossless** (the in-memory
`RUNS` dict stays authoritative; tenancy/version tables are an additive derived layer; superseding a version
PRESERVES the old one until an explicit prune); **honest** (degrade-and-record everywhere; durability off ⇒
byte-identical prior behavior; a cross-tenant fetch returns 404 and NEVER leaks existence; a superseded+pruned
version is an honest 410 Gone); **change-verification** (warrant = the rubric's tenancy-gap finding, cited).

Net: **+421 / −58** lines, one file (`baltor_admin_demo_server.py`, now 6385 lines). Still allowlisted in
`architecture/monolith_allowlist.json`; `check_monolith_allowlist --self-test` stays green (the allowlist's
descriptive `current_lines: 5445` is now stale — refresh is for the `architecture/` owner, out of this
surgical scope).

---

## 1. Tenant isolation (the real gap)

**Design.** There is no real multi-tenant identity in this demo yet, so a `tenant_id` is threaded end-to-end
that **DEFAULTS to one `"demo"` tenant** (the current public demo is byte-identical) but is **honored
everywhere**, so isolation is REAL the moment a different tenant is supplied. This is request-scoped
*attribution*, NOT authentication — `_authed` (`OH_SHOWCASE_TOKEN`) still gates writes; per-tenant key auth
is the next layer (`service-auth-and-consumption-model.md`'s orphaned `/service/*` handshake). I did NOT use
the `pipeline_runtime.isolation.resolve` seam the P1 critique mentioned: that seam yields a **separate per-tenant
db/ledger** and lives in `do_POST`'s `/api/dev/*` path; the gateway's `RUNS`/handles ride the SHARED WAL db +
the in-memory `RUNS` dict, so the correct, lower-blast-radius isolation is a `tenant_id` **column + predicate**
on those shared structures (a per-tenant *namespace*, not a per-tenant *database*). A separate-db split is a
future scale step, noted below.

**The tenancy seam (`scripts/baltor_admin_demo_server.py`):**

| Piece | Lines | What it does |
|---|---|---|
| Constants (`DEFAULT_TENANT`/`TENANT_HEADER`/`TENANT_PARAM`/`DURABLE_VERSIONS_MAX`) | 686–690 | single source; no magic literals |
| `gateway_runs`/`gateway_receipts` gain a `tenant_id` column + the new `gateway_versions` table | 700–741 | incl. a lossless `ALTER TABLE … ADD COLUMN` so a **P1-era db upgrades in place** (pre-P2 rows read back as `demo`) |
| `normalize_tenant` | 817–823 | one rule: empty → `DEFAULT_TENANT`; else `compact_id` (`[a-z0-9-]`, so a tenant id can't inject path/SQL weirdness) |
| `resolve_tenant(parsed, header, body)` | 825–840 | `?tenant=` → `X-OHH-Tenant` → body field → `DEFAULT_TENANT` (mirrors how `_authed` resolves the token) |
| `run_tenant` / `run_visible_to` / `latest_run_for_tenant` / `run_for_tenant` | 842–872 | the per-tenant replacements for the global `latest_run()`; `run_for_tenant` returns `None` for a cross-tenant `run_id` → callers emit 404 |
| `tenant_id` added to the run dict | `build_run` 2256/2272, `create_background_run` 2111/2124 | every run is OWNED by a tenant; persisted in `body_json` AND the column |
| `gateway_receipt(..., tenant_id=)` | 972–1009 | receipts now carry + persist `tenant_id` (isolation provenance) |
| `Handler._tenant(parsed, body)` | 5382–5385 | the request-edge seam |
| Routes wired: GET search/fetch (5615/5627), POST search/fetch (5958/5978), run-create (6115) | — | each resolves the tenant and uses `run_for_tenant`; a `ctxv://` fetch is resolved run-independently |

**Isolation guarantee.** `context_search_payload` (3855) and `context_fetch_payload` (3945) take `tenant_id`
and (a) honor a passed-in `run` ONLY if `run_visible_to(run, tenant)`, (b) fall back to
`latest_run_for_tenant(tenant)` — **never** the global `latest_run()`. So a tenant can never search/fetch
another tenant's index, and an empty-namespace search/fetch returns a clean 404 (no existence leak).

> **Scope note (honest):** the LOWER-risk read surfaces that do NOT return raw ingested bytes — `/glossary`,
> `/dimensions`, `/status`, the dashboard renderers, exports — still use the global `latest_run()`. For the
> default single-tenant demo this is byte-identical. The strict P2 target is "RUNS/handles + the raw-content
> fetch + ctxv://", which is fully isolated; tenant-scoping those secondary reads is a follow-up (below).

## 2. `ctxv://` versioned (immutable) fetch

**Design.** `ctx://` stays "latest" (mutable). On every successful `ctx://` fetch, the served bytes are
**pinned** as an immutable `ctxv://base@<hash16>` (same shape as the context-object versions already minted at
`add_object`, ≈ line 2737) into a durable `gateway_versions` table, and the fetch response returns the
`version_handle` so an agent can re-fetch the EXACT bytes later. A `ctxv://` fetch:

- **present + this tenant** → 200, returns the pinned body **byte-identical even if the live content changed**;
- **superseded and pruned** → **410 Gone** (honest: the version existed, the lossless retention window passed);
- **never seen by this tenant** → **404** (existence never leaks across tenants — the base-existence probe is
  tenant-scoped).

**Lossless supersession.** When a newer hash is pinned for the same `(tenant, base)`, older versions are marked
`superseded_at` but **KEPT** (still fetchable) until `prune_versions()` trims by age past `DURABLE_VERSIONS_MAX`
(default 5000). Nothing truth-bearing is destructively overwritten; the loser keeps lineage to the winner.

**The versioning code:**

| Piece | Lines |
|---|---|
| `gateway_versions` schema (`version_handle` PK, `tenant_id`, `base_handle`, `content_hash`, `body_json`, `superseded_at`) | 730–736 |
| `versioned_handle(base, hash)` — the single source of the `ctxv://base@<hash16>` form | 875–882 |
| `pin_version(...)` — idempotent pin; supersede-but-keep older; best-effort (durability off ⇒ `''`, ctx:// still works) | 884–920 |
| `prune_versions()` — LRU by `created_at`; pruned rows then fetch as 410 | 922–935 |
| `fetch_pinned_version(tenant, ctxv://)` → `('ok'|'gone'|'missing', row)` | 938–970 |
| `context_fetch_payload` ctxv:// branch + ctx:// pin-on-fetch + `status` field | 3945–4046 |
| Route 410/404 mapping (`code = 200 if ok else (410 if status=='gone' else 404)`) | GET 5645, POST 5990 |

The fetch payload now returns a `status` (`ok`/`gone`/`missing`/`no_run`) the routes map to HTTP codes, plus
`version_handle` (on a ctx:// fetch) and `immutable: true` / `base_handle` (on a ctxv:// fetch).

---

## 3. The isolation trace (live, temp port, temp db; `:9301` untouched)

```
temp port=36383  temp db=/tmp/.../durable.db   (live :9301 untouched)
1) POST /admin-demo/runs (tenant=acme)                       -> HTTP 303
2) GET  /context-gateway/search?tenant=acme                  -> tenant_id=acme
     handle = ctx://baltor/adm-fcf5ee3a7a/component/file-path=pasted-context-txt/page=1/component-id=component-001
3) GET  /context-gateway/fetch?tenant=globex&handle=<acme>   -> HTTP 404   # B cannot fetch A's handle (no leak)
4) GET  /context-gateway/fetch?tenant=acme&handle=<acme>     -> ok=True
     version_handle = ctxv://baltor/adm-fcf5ee3a7a/.../component-id=component-001@320ed873d56af45e
5) GET  /context-gateway/fetch?tenant=acme&handle=<ctxv://>  -> ok=True immutable=True   # pinned version
6) GET  /context-gateway/fetch?tenant=globex&handle=<ctxv://>-> HTTP 404   # B cannot fetch A's ctxv:// either
7) POST /admin-demo/runs (no tenant) + search (no tenant)    -> ok=True tenant_id=demo   # default byte-identical
   server stderr tracebacks: (none)
```

**Pinned-version-survives-a-live-change (in-process, through the real `context_fetch_payload`):**

```
PIN v1 = ctxv://baltor/adm-f2898912ef/.../component-001@4d4d94bced7111af
  ctx:// bytes #1: 'Escalations acknowledged within 10 business days.'
-- mutate the live component text for the SAME ctx:// base --
PIN v2 = ctxv://...@f45a31d7ac65d0fb   (changed vs v1: True)
  ctx:// bytes #2: 'Escalations acknowledged within 30 business days (UPDATED).'
FETCH ctxv:// v1 -> ok=True immutable=True
  pinned v1 bytes: 'Escalations acknowledged within 10 business days.'   # STILL the original
RESULT: ctxv:// v1 returns the ORIGINAL pinned version AFTER the live content changed: PASS
```

**P1→P2 db migration (lossless, against a P1-shaped db with no `tenant_id` column):**

```
gateway_runs has tenant_id column now: True      # ALTER TABLE added it
gateway_receipts has tenant_id column now: True
pre-P2 run rehydrated: True  tenant resolves to: demo
visible to demo: True  visible to globex: False  # old global run = the demo tenant, isolated from others
P1->P2 MIGRATION: PASS
```

---

## 4. Test PASS lines

In-file proof: `python3 scripts/baltor_admin_demo_server.py --self-test` (`_self_test` at 6142). Ran **3×** →
identical PASS, 21/21 checks. New P2 proofs (alongside the preserved P1 ones):

```
[ok] P2 item5a: ctxv:// pin returns C1 byte-identical AFTER the live content changed to C2
[ok] P2 item5b: superseding is LOSSLESS — old version superseded_at set but STILL fetchable
[ok] P2 item5c: latest ctxv:// for the same base is the NEW content C2 (distinct handle)
[ok] P2 item5d: after prune past the cap, the old version is 410 GONE while the new one stays ok
[ok] P2 item5e: a ctxv:// version is tenant-scoped — wrong tenant → missing (404), no leak
[ok] P2 item6: search is tenant-scoped (acme pack tagged tenant_id=acme)
[ok] P2 item6: tenant B (globex) CANNOT fetch tenant A's handle → 404 (no existence leak)
[ok] P2 item6: tenant B search never returns tenant A's run (own empty namespace → 404)
[ok] P2 item6: SAME-tenant fetch works (acme → 200) and returns a ctxv:// version_handle
[ok] P2 item6: ctxv:// pinned-version fetch works over HTTP for the owner (200, immutable=True)
[ok] P2 item6: tenant B CANNOT fetch tenant A's ctxv:// version → 404
PASS — ... P2 — gateway is tenant-isolated (B cannot fetch A: ctx:// AND ctxv:// → 404), ctxv:// returns the
       pinned version after a live content change (lossless supersession; 410 only after prune),
       default-tenant path byte-identical.
```

**Wider gate (each 2×, `PYTHONPATH=.`):** every `check_*baltor* / *context* / *gateway* / *admin* /
*monolith*` script — 50+ scripts — passes on both passes EXCEPT one **pre-existing** red,
`check_baltor_design_system` (`A: SPA root is the Baltor dir-d (teal) scope`), a `web/` SPA-scope issue
unrelated to this backend file. **Proven not mine:** `git stash`ing the change reproduces that failure
identically on clean HEAD (exit 1, same message), then `git stash pop` restores the change. `py_compile`
clean across all runs.

---

## 5. Is this now customer-grade? — what's the next gap

This pass makes the gateway **tenant-isolated and version-immutable** — the two gaps the rubric named. It is
customer-grade for the **isolation contract** (one tenant can never see another's handle, ctx:// OR ctxv://,
and gets a clean 404, never an existence leak) and the **immutability contract** (a `ctxv://` is byte-stable
under live change, with honest 410 on pruned versions and lossless supersession). The critique, deepest-first:

- **Attribution ≠ authentication (the real remaining gap).** `tenant_id` is *supplied* by the caller
  (`?tenant=`/header/body); nothing yet *proves* a caller IS that tenant. The isolation is correctly enforced
  on whatever tenant is asserted, but a hostile caller can assert `tenant=acme`. The next layer is per-tenant
  **key** auth: bind `_authed` (today a single global `OH_SHOWCASE_TOKEN`) to a per-tenant credential — the
  Phase-1 is the orphaned `/service/*` handshake in `service-auth-and-consumption-model.md`. Until then this is
  honest tenancy *plumbing*, not access *control*.
- **One shared SQLite namespace, not per-tenant stores.** Isolation is a `tenant_id` column + predicate on one
  WAL db. This is correct and lossless, but a noisy/large tenant shares the file and the `RUNS` cap. The
  rubric's "per-tenant stores" + the SQLite→Postgres path is the scale move (and would let the
  `pipeline_runtime.isolation.resolve` per-tenant-db seam back the gateway too).
- **Secondary reads still global.** `/glossary`, `/dimensions`, `/status`, exports, and the dashboard
  renderers use the global `latest_run()` — byte-identical for the demo, but they should become tenant-scoped
  for true multi-tenant serving (they don't return raw ingested bytes, so lower risk; deferred deliberately).
- **Version GC is age-only.** `prune_versions()` is LRU by `created_at` with a flat cap; a real product wants
  per-tenant quotas and a retention policy tied to the source's volatility, plus the pinned `content_hash` as
  the verifiable link inside the receipt envelope (P1's "one OTel-compatible receipt envelope" critique).
- **Carry-overs from P1 (unchanged here):** keyword-only retrieval (`vector search: False`); the four-receipt
  fragmentation; the monolith split (gateway → run engine → renderers). None block the P2 contracts.

**Verdict:** the gateway now has the two hard correctness properties a customer-grade context layer needs
(isolation + immutable versioned fetch), proven end-to-end. The next single highest-leverage step is
**per-tenant key auth** so the asserted `tenant_id` becomes a *verified* identity — that turns this plumbing
into a sellable boundary.
