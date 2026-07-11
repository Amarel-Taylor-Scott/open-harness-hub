# AI Done Right — Portfolio Functionality + Wiring Spec

> Generated from the wiring-review workflow (wf_52602c56-586), then maintained by hand. It traces, for every surface page/view/button, the full loop (UI handler -> seam -> backend handler -> state) with file:line evidence, and gives each element its purpose, problem, solution, product-market fit, dependencies, what it communicates with, wiring status (wired/partial/stub/broken), and gap.
>
> The machine-checkable slice of this lives in `architecture/required_functionality.json` (checked by `scripts/check_required_functionality.py`): 'page X requires functionality Y' as graph nodes with deterministic check-edges. Update both when a gap is closed.

---

# AI Done Right — Product + Wiring Spec (by Surface · by Page · by Flow)

> Source: per-area page/flow traces for the three live surfaces. All wiring facts (seam paths, backend `file:line`, status) are taken verbatim from the traces. Purpose / Problem / PMF framing is product articulation layered on top of those facts. Where a trace says "none"/"NONE", no seam or backend was found — not inferred.

Status legend: **wired** = UI→seam→backend→persist all present and exercised · **partial** = seam + backend exist but UI under-calls them or falls back to fixtures · **stub** = UI-only theater, no seam/backend · **broken** = control exists but handler is a dead no-op.

---

## SURFACE 1 — Identity & Accounts (cross-cutting)

Bundle: `dist/sites/aidoneright-design` (kit `oh-site.jsx`, client `oh-identity.js`) → backend `scripts/identity_local_service.py` over `/api/identity/<realm>/*`. 24 realms from `architecture/identity_realm_registry.json`. This is the only genuinely production-shaped backend in the portfolio (hash-only key storage, sliding-window throttle, append-only audit ledger, atomic persistence, real `--self-test`).

### Pages

| Route | Component | Purpose |
|---|---|---|
| /signup | OhAuth (signup) | Create a realm-scoped account |
| /signin | OhAuth (signin) | Log into a realm; per-realm session in localStorage |
| /forgot | OhAuth (forgot) | Password-reset request |
| /dashboard | OhDashboard | Signed-in landing (stats/activity/plan/quick-start) |
| /onboarding | OhOnboarding | Post-signup checklist |
| /keys | OhApiKeys | Mint / list / revoke per-realm API keys |
| /team | OhTeam | Invite teammates, manage roles |
| /billing | OhBilling | Plan, usage meter, invoices |
| /usage | OhUsage | Activity metrics for billing period |
| /settings | OhSettings | Profile / preferences |
| /audit | OhAuditLog | Receipts: served packs, verifications, key actions |
| /notifications | OhNotifications | Inbox of changes/escalations/results |
| /contact | OhContact | Contact / sales form |

### Flows

**Register / signup** — `wired`
- Purpose: create a real per-realm account and land authenticated.
- Problem solved: a tenant needs a durable identity scoped to one product realm (no cross-realm SSO leakage).
- Solution: `submitAuth` validates email + ≥8-char pass, pings `available()`, then `OHIdentity.signup` chains `register` → per-step `onboard` → `login` (`oh-identity.js:40-47`); backend `_dispatch 'register'` → kit `realm.register` + `rt.save()` + verify-email port (`identity_local_service.py:391-402`).
- PMF: every B2B AI tenant needs accounts; realm scoping is the table-stakes entry to the paid plane.
- Dependencies: identity service, realm registry, verify-email port, kit OhAuth.
- Communicates with: `POST /api/identity/<realm>/register` then `/onboard` then `/login` → `identity_local_service.py:391-407`.
- Status: **wired** (confirmed `realm-baltor.json` has real `acct_*` rows; audit row appended).
- Gap: signup **Name** field (`oh-site.jsx:439`) is collected but never sent (register takes only identifier+secret) — display name dropped. Verify-email uses a console adapter that renders-but-does-not-send and keys the link on `account_id` (no one-time token). Onboarding steps auto-complete silently.

**Login** — `wired`
- Purpose / Problem: authenticate an existing user against the correct realm with brute-force protection.
- Solution: `submitAuth → OHIdentity.login` (`oh-site.jsx:405`) → `_dispatch 'login'` sliding-window throttle + `realm.login`, generic 401 (`identity_local_service.py:408-424`).
- PMF: secure login is non-negotiable for any account that holds API keys / governed data.
- Communicates with: `POST /api/identity/<realm>/login` → `:408-424`.
- Status: **wired**. Gap: no UI surfaces lockout state; error copy generic.

**Logout** — `wired` · `POST /api/identity/<realm>/logout` → `:425-429`. Server pops `realm.sessions[session_id]` + saves; client clears localStorage best-effort. Gap: client clears even if network call fails (server pop is real).

**Session persistence / validate** — `wired` (but not enforced)
- Purpose: re-verify session on load, degrade to signed-out if expired (TTL 3600s).
- Communicates with: `POST /api/identity/<realm>/session/validate` → `:430-436`.
- Status: **wired** mechanism. Gap: **no route GATES /dashboard on `validate()`** — an unauthenticated user reaching /dashboard directly still renders the fixture-filled console. Validation available, not enforced.

**Preview-mode fallback (service down)** — `wired`
- Purpose: when identity is unreachable, honestly flag an unsaved preview instead of faking an account.
- Solution: `enterPreview` sets `sessionStorage 'oh-preview'='1'`, navigates /dashboard, `OhPreviewBanner` warns (`oh-site.jsx:270-281`); only probe is `GET /api/identity/health` (`:511-513`).
- Status: **wired** (honest). Gap: by design /dashboard still renders fully populated with fixtures for a never-authenticated user.

**API key — mint** — `wired`
- Purpose / Problem: a signed-in user needs a real per-realm secret services can verify.
- Solution: `OhApiKeys.mint → OHIdentity.mintKey(realm,['read'])` (`oh-site.jsx:678-695`) → `_dispatch 'api-keys/mint'` validate_session + `rt.mint_key` (hash-only at rest, raw shown once) + save (`identity_local_service.py:437-445`).
- PMF: programmatic access is how AI customers actually consume; revocable keys are an audit requirement.
- Communicates with: `POST /api/identity/<realm>/api-keys/mint`.
- Status: **wired**. Gap: realm inferred by scanning localStorage for first `oh-session-*` (`:662-673`); no scope picker (hardcoded `['read']`).

**API key — list** — `partial`
- Purpose: on open, show the account's REAL keys (prefix/created/last-used/revoked).
- Communicates with: `OHIdentity.listKeys` (`oh-identity.js:61`) + backend `api-keys/list` (`:446-453`) — **both exist, UI never calls listKeys on mount**.
- Status: **partial**. Gap: a real key minted in a prior session vanishes after reload while 3 fake `sk_live_9f2c / sk_live_3b71 / sk_test_a1f0` always show. Fix = one `useEffect`.

**API key — revoke** — `partial`
- Communicates with: `POST /api/identity/<realm>/api-keys/revoke` → validate_session + ownership check + `revoked_at` + save (`:461-471`).
- Status: **partial**. Gap: revoke only wired on `k.real` rows; the always-present fixture rows render a "Revoke" link with `onClick` undefined (dead).

**Onboarding checklist page** — `stub`
- Purpose: drive real `onboarding_steps` from the account record, mark each via `/onboard`, gate the app until done.
- UI: `OhOnboarding` "Start" → `navigate('/app')`, no per-step call (`oh-site.jsx:902-923`). Backend `/onboard` exists (`:403-407`) but this page never calls it.
- Status: **stub**. Gap: decorative; first step hardcoded "Done"; signup() already auto-completes all steps so the page can never reflect real progress.

**Password reset / forgot** — `stub`
- Purpose: issue a one-time token, deliver via email port, accept new passphrase, rotate credential ref.
- UI: `onClick={() => setSent(true)}` flips to "check your email"; **no client method, no backend endpoint** (grep: zero reset/forgot in `oh-identity.js`; no reset route in `identity_local_service.py`).
- Status: **stub** (pure theater). Gap: a real-account user genuinely cannot recover a password. **Highest-severity account gap.**

**Team / member management** — `stub`
- Purpose: invite teammates (email→pending member), assign roles, manage/remove, scoped sessions.
- UI: no handlers on any control; renders 4 fixtures (Ada Lovelace / Alan Turing / Grace Hopper / invited@company.com). No member/team/invite endpoint exists; no multi-user-per-account concept in backend.
- Status: **stub**.

**Billing** — `stub` · plan/usage/invoices are hardcoded caller props (`teleon-main.jsx:415`: Team $249, usagePct 62, three "Paid" invoices). "Manage plan"/"Download" have no onClick. No billing service.

**Usage metrics** — `stub` · `OhUsage` renders hardcoded props (`teleon-main.jsx:417`: Runs 4,120 / Promotions 38 / Rollbacks 6 / Eval hrs 212). No fetch.

**Settings** — `stub` · inputs are `defaultValue` only, prefilled "Ada Lovelace"/"ada@company.com"; `OhSwitch onToggle={() => {}}`. No profile/settings endpoint. Nothing persists.

**Audit log** — `stub` (closest-to-wirable)
- Purpose: surface the account's REAL signed receipt stream.
- Backend: audit IS written (`IdentityService.audit → audit-events.jsonl`, `:313-317`; ~255KB real events) but **no list/read endpoint** and no client method.
- Status: **stub**. Gap: genuine append-only ledger exists; UI shows 5 fixture rows. Needs a read endpoint + a `useEffect`.

**Notifications** — `stub` · no onClick on "Mark all read"; fixtures incl. "API key used from a new IP · 8.8.8.8". No backend.

**Contact / sales form** — `stub` · `onClick={() => setSent(true)}` only; fields uncontrolled; nothing leaves the browser.

**Service-to-service connection (handshake/verify/revoke)** — `wired` (no UI)
- Purpose: cross-realm service auth (Baltor→Teleon) with scoped tokens + receipts.
- Communicates with: `POST /api/identity/<from>/service/{handshake,connections,verify,revoke}` (Bearer secret) → `IdentityService.service_handshake/_dispatch_service` (`:264-387`); persists to `service-connections.json`, token shown once, receipts issued.
- Status: **wired** backend, proof-tested. Gap: **no front-end surface** — operators cannot mint/list/revoke service connections from any page.

---

## SURFACE 2 — Teleon (runtime SaaS)

Served app: `_repos/teleon/frontend/teleon-main.jsx` over the showcase (`scripts/showcase/server.py:125-127`), kit `_repos/teleon/frontend/kit/oh-site.jsx`, single real seam `window.TeleonLive` (`_repos/teleon/frontend/teleon-live.js`) → `/api/teleon/*` → `scripts/teleon_local_runtime.py`. (Note: `dist/sites/aidoneright-design/teleon/teleon-main.jsx` is the DESIGN HANDOFF spec — fully hardcoded, NOT served, NOT wired.)

### Pages

| Route | Name | Purpose | Wiring note |
|---|---|---|---|
| / /how /lifecycle | Landing | Hero/How/Lifecycle/Ecosystem/CTA; "Start free"→/signup | static |
| /fits | Where Teleon fits | Honest landscape vs LangGraph/Temporal/DSPy | static |
| /signin /signup /forgot | Auth | OhAuth vs realm identity (`oh-identity.js`) | the session gate the runtime validates |
| /dashboard | Dashboard | Stats + activity + plan mini + quick start | partial |
| /app | Capabilities table | Rollup + caps table | wired read |
| /runs | Build a capability | Purpose textarea + criteria toggles + Build | partial |
| /evidence | Evidence | Static prose; no receipts rendered | stub |
| /keys | API keys | OhApiKeys real mint/revoke + 3 fixtures | partial |
| /team | Team | Hardcoded members + dead buttons | stub |
| /audit | Audit log | Hardcoded receipt rows | stub |
| /notifications | Inbox | Hardcoded notifications | stub |
| /billing | Billing | Hardcoded Team $249 + 3 invoices | stub |
| /usage | Usage | Real sparkline via TeleonLive.usage() else fixtures | partial |
| /settings | Settings | Hardcoded Ada profile + 2 no-op switches | stub |
| /onboarding | Onboarding | OhOnboarding (kit) | stub |
| /registry | Library | Static prose; never queries /registry seam | stub |
| /pricing | Pricing | Static Starter $0 / Team $249 / Enterprise | static |
| /docs /status /changelog /terms /privacy /about /contact /cases | Marketing/info | shared kit | static |

### Flows

**Build a capability (Build button)** — `partial` — the core write path
- Purpose: type a purpose + criteria → synthesize a NEW capability, run on real examples, train+holdout gate, promote or roll back.
- Problem solved: teams want verified, versioned capability units instead of unaudited prompt-in-app.
- Solution (what actually runs): `onClick` sets `phase='running'`, animates 6 LIFECYCLE rows via setTimeout (cosmetic, `teleon-main.jsx:296-300`), AND calls `TeleonLive.run()` **with no argument** → `POST /api/teleon/teleon/runs {capability_id:'cap-dates', session_id}` (`teleon-live.js:76-93`) → `Handler.do_POST` validates session, `RT.submit_run(background=False)` → `_run_to_completion` executes the cap-dates suite, applies train+holdout gate (PROMOTE_AT 0.90), bumps version, on promotion auto-compiles+registers a deployable unit (`teleon_local_runtime.py:755-794, 502-604, 621-643`). Persists caps/runs/receipts/compiled-units to `dist/local-services-state/teleon-runtime/`.
- PMF: the eval-gated promotion + receipts are the differentiator vs raw orchestration frameworks; this is what a compliance-minded buyer pays for.
- Dependencies: teleon runtime, identity session, a healthy model route (else falls to deterministic reference impl), state dir.
- Communicates with: `POST /api/teleon/teleon/runs` → `teleon_local_runtime.py:755-794`.
- Status: **partial**. Gap: the **purpose textarea + 3 criteria toggles are purely cosmetic — never sent**; `run()` called with no id so it ALWAYS re-runs the global pre-seeded `cap-dates` and **never builds the typed purpose**. The 6 lifecycle rows are setTimeout theater independent of the real run. No new capability is ever created.

**Capabilities table load** — `wired` (read) but global
- Communicates with: `GET /api/teleon/teleon/capabilities` (open read, no session) → `teleon_local_runtime.py:737-738`.
- Status: **wired** read. Gap: caps are **GLOBAL** (one `capabilities.json`, no session scoping) — every account sees the same 4 seeded caps (cap-dates/redact/json-guard/cite). "Evidence →" just `navigate('/evidence')` with no cap id. Runtime-down → marketing CAPS fixtures (cap-usury v12 etc.).

**Dashboard stats + Recent activity** — `partial`
- Communicates with: stats from cached caps; activity/usage `GET /api/teleon/teleon/runs?session_id=…` (session-gated) → `:739-751`.
- Status: **partial**. Gap: `stats()` falls back to fixtures (38 promotions, avg 0.90) when runtime down; `activity()` returns null for a brand-new (zero-run) account → **fake fixtures incl. "State usury-rate finder promoted 0.96" and "Invoice paid $249.00"** (`teleon-main.jsx:397-402`). Plan mini `{name:'Team', usagePct:62}` ALWAYS hardcoded — no seam (`:403`).

**Create / revoke API key** — `partial` — same identity plane as Surface 1. Real mint/revoke via `OHIdentity.mintKey/revokeKey` (realm "teleon"); 3 fixture rows always prepended (`kit/oh-site.jsx:652-656`), their Revoke inert.

**Billing / Plan / invoices** — `stub` · no seam, no billing service. Hardcoded Team $249/mo, 62%, invoices May/Apr/Mar 2026 all $249 Paid; "Manage plan"/"Download" dead. Shown to brand-new accounts.

**Team / members / invite** — `stub` · no seam/backend. Hardcoded Ada/Turing/Hopper/invited; all buttons inert.

**Audit log** — `stub` · runtime DOES persist `receipts.jsonl` + run events but UI never reads them here. Hardcoded Baltor-flavored rows; footer falsely claims "signed and exportable."

**Notifications / Inbox** — `stub` · hardcoded ("38 promotions·6 rollbacks", "API key used from 8.8.8.8"); Mark-all-read inert.

**Settings (profile + preferences)** — `stub` · `defaultValue` inputs hardcoded "Ada Lovelace"/"ada@company.com"; `onToggle={() => {}}`. "Auto-rollback" shown ON but changes nothing in the runtime gate.

**Evidence / review** — `stub`
- Purpose: per-capability evidence trail — each version tried, train/holdout pass-rates, per-example receipts with input/output hashes + promote/rollback decision.
- Communicates with: backend EXPOSES `GET /api/teleon/teleon/evidence?run_id=…` → `RT.receipts_for(run_id)` (`teleon_local_runtime.py:752-753, 684-687`) — **UI never calls it**; the link passes no cap/run id.
- Status: **stub** (real receipts exist on disk + over seam, never displayed). Review/HITL approval not built.

**Usage charts** — `partial` · `GET /runs?session_id=…` gives real run count / exec time / 7-bucket spark when runs exist. Gap: zero-run account → fixtures leak ("4,120 Runs·30d", "212 Eval hrs"); "Eval compute (hrs)" is a fixture metric the seam never provides.

**New capability / Quick-start CTAs** — `wired` · pure client navigation to /runs, /evidence, /keys (`teleon-main.jsx:271,404-407,439`). Correct.

**Library / registry page** — `stub` · static prose; a `/registry` proxy exists in the showcase but this page never queries it. No bill-of-materials of components a capability used.

---

## SURFACE 3 — Baltor (applied context product)

Static design-handoff prototype at `dist/sites/aidoneright-design/context-enrichment/`. `Context Enrichment.html` loads React + in-browser Babel from unpkg and transpiles `ce-*.jsx` client-side. **ZERO network calls anywhere** (grep for fetch/XHR/api returns only display strings). ALL data is fixtures in `ce-store.jsx` + inline literals. README states it outright ("All data is fixtures… Wire these to real services"). No auth gate — the entire logged-in workspace renders unauthenticated as one hardcoded "Acme · Compliance" Pro tenant.

### Pages

| Route | Name | Purpose |
|---|---|---|
| / | Landing | Hero/how/verify-moat/commons/tiers/serve-preview/CTA; Hero A/B via window.OHExp |
| /why | WhyPage | Marketing positioning |
| /engine | EngineMarketing | Animated canvas context-lifecycle (6 stages) over ENG_STAGES |
| /pricing | PricingPage | 3 hardcoded PLANS; every CTA → /ingest |
| /docs | DocsPage | Overview/Guides/Reference/Demos/API tabs (intended REST contract, not live) |
| /signin /signup /forgot | Auth (kit) | Kit.OhAuth under Baltor scope; no Baltor-side network code |
| /contact /about /cases /cases/:id | Marketing | OhContact/OhAbout/OhCaseStudies fed CASES.baltor fixtures |
| /dashboard /app | DashboardPage | OhDashboard + 4-stage engine grid, hardcoded |
| /sources | SourcesPage | Connect-source form + linked-sources from SOURCES const |
| /pipeline | PipelinePage | 6-stage engine RAF progress over PIPE_STAGES |
| /pipeline/:id | PipelineStage | Per-stage detail from PIPE_STAGES |
| /corpora | CorporaPage | 6 hardcoded CORPORA + ROLLUP |
| /ingest | IngestPage | Add-a-source wizard: setup→refining(timer)→done(hardcoded sizes) |
| /c/:id | CorpusDetail | Tiers/Provenance/Serve/Compliance/Settings from CORPUS_BY_ID |
| /serve | ServePage | Serve console → MOCK_CHUNKS + fake 7/7 pipeline |
| /verify | VerifyPage | Reconciliation queue over CONFLICTS fixture |
| /commons | CommonsPage | Oracle-corpus marketplace from COMMONS fixture |
| /governance | GovernancePage | Provenance/audit derived from CORPORA fixture |
| /audit | AuditPage | OhAuditLog, 5 hardcoded rows |
| /settings | SettingsPage | OhSettings, toggles local useState |
| /billing | BillingPage | OhBilling, hardcoded plan + 4 invoices |
| /usage | UsagePage | OhUsage, hardcoded rollup + spark bars |

### Flows

**Ingest / connect a source (core write path)** — `stub`
- Purpose: turn a source descriptor into a real corpus (fetch→parse→chunk→fingerprint→raw/compressed/hyper tiers→citation anchors→persisted row).
- Problem solved: regulated teams need governed, tiered, provenance-anchored corpora — not a raw RAG dump.
- Solution today: `IngestPage.start()` sets `phase='refining'`; a `useEffect` + `setTimeout(620ms)` walks step 0→6 over REFINE_STEPS, then `setPhase('done')` (`ce-app.jsx:51-124`). Done panel shows hardcoded raw 1.18GB/compressed 402MB/hyper 91MB (`:112`); "Open corpus →" → fixture `/c/acme-policy` (`:117`).
- PMF: this IS the product's value creation; nothing is paid for until ingest is real.
- Communicates with: **none** — input value never read after typing.
- Status: **stub**. Gap: timed animation; no upload/crawl/parse/persist/real sizes. The 4 checkboxes are decorative `defaultChecked` with no handler.
- North star: `POST /api/baltor/ingest` (or `/v1/corpora`) → fetch+parse+chunk+fingerprint, build tiers, anchor citations, write Postgres + object storage; progress via SSE/websocket; "Open corpus" opens the new id.

**Connect source on /sources + "Link & run engine"** — `stub` · button `onClick={() => navigate('/pipeline')}` (`ce-pipeline.jsx:57`); linked-sources table is static SOURCES (`:31-36`); typed value discarded. No connector handshake/persistence. North star: connector OAuth via the credential plane, persist source record, kick real engine run.

**Engine pipeline run** — `stub` · `usePipelineProgress()` RAF fills bars to fixed targets over ~6s (`ce-pipeline.jsx:81-100`); `EngineCanvas()` animates particles (`ce-engine.jsx:33-61`). Metrics ("44 conflicts","13× tokens","21.6k packs/day") are literals. No engine, run record, or receipts.

**Serve console — run a query** — `stub`
- Purpose: retrieve from selected corpus/tier, rerank, freshness-check, verify each chunk vs live sources, return cited chunks + receipt, hold contradicted/stale chunks out.
- Solution today: `setRan(true)` (`ce-app.jsx:271`); 7-step pipeline flips all ✓; renders the 3-element MOCK_CHUNKS (`:228-232`), identical regardless of corpus/tier/destination/query. The shown `GET /v1/corpora/{id}/serve?...` is a syntax-highlighted `<div>` (`:272-275`), not a request.
- PMF: verified-at-serve-time citation is the entire moat claim; this is what agents would pay to call.
- Communicates with: **none**.
- Status: **stub**. Gap: query ignored; same 3 chunks always; no retrieval/verification/real citations.

**Verification / reconciliation queue (HITL)** — `stub`
- Purpose: resolve a conflict → update/quarantine affected chunks, record who/what/policy, emit audit receipt; reg-change feed + watched-source freshness from a live CDC/watcher.
- Solution today: `act(id, how)` sets a local `resolved` map; card renders "✔ update applied" (`ce-app.jsx:316-318, 379-389`). Code comment literally says "so the actions feel live."
- Communicates with: **none**. CONFLICTS/VERIFY_ROLLUP/REG_CHANGES/WATCHED are fixtures in `ce-store.jsx`.
- Status: **stub**. Gap: the whole adversarial-verification moat is hardcoded conflict cards; lost on refresh.

**Corpus detail — Download bundle / Download tier / Emit artifact** — `broken`
- Purpose: stream a signed corpus bundle / tier export / compliance artifact (AIBOM CycloneDX, EU AI Act dossier, C2PA manifest, fidelity record).
- UI: these `<button>`s have **NO onClick** (`ce-app.jsx:149, 170, 209`).
- Status: **broken** (dead buttons). The regulator-facing deliverable is non-functional.

**Commons — Add to workspace / Verify by hash** — `stub` · "Add to workspace" → `navigate('/ingest')` (`ce-app.jsx:457`); "Verify by hash" has **NO onClick** (`:458`) despite being the central trust claim. COMMONS hashes/subscriber counts/lastVerified are fixtures.

**Authentication (sign in / sign up / forgot)** — `stub` · routes to `Kit.OhAuth brand=Baltor` (`ce-main.jsx:31-41`); **no fetch in any ce-*.jsx**, no `/api/identity` seam referenced. **No auth gate**: every workspace route renders fully unauthenticated showing the same Acme tenant.

**Settings — toggles / rotate keys / edit fields** — `stub` · `OhSwitch` flips local `tog` useState (`ce-app.jsx:474-475`); "Rotate keys" has **NO onClick** (`:489`); inputs uncontrolled `defaultValue` never read; serving token `ctx-••••••••a41e` and `mcp.baltor.ai/acme` are static strings.

**Billing / Usage / Dashboard / Audit** — `stub` · shared Oh* components fed inline literal props (`ce-app.jsx:501-518, 593-641`). Every invoice, usage bar, activity row ("Served acme-policy to Claude Code · 40s ago"), audit receipt is fabricated. No telemetry pipeline.

**Theme toggle** — `wired` · `useTheme().toggle` → `localStorage('baltor-theme')` (`ce-store.jsx:30-38`); survives refresh. The ONLY genuinely persisted action in the whole surface.

---

## (A) North-star per product

**Identity & Accounts** — A cross-cutting, realm-scoped identity plane where every AI Done Right product gets durable accounts, recoverable credentials, revocable API keys with real scopes, a multi-user org model (invite→role→scoped session), and a single signed audit/receipt stream — all gated so no authenticated view ever renders before the session is validated, and no account ever sees another tenant's data. The backend is already production-shaped; the north star is to finish the read paths (key list, audit read), the recovery path (password reset), the org model (teams), and to enforce the session gate.

**Teleon** — A purpose-driven, eval-gated capability runtime where typing a NEW purpose + success criteria synthesizes a NEW, per-account capability, runs it on real examples under a train+holdout promotion gate, promotes or rolls back with versioned receipts, and exposes the full capability experience — generated code, version/fork history, guardrail/license selection, exports, runtime metadata, and a component bill-of-materials. The runtime/eval/gate/promote engine is real for the seeded `cap-dates`; the north star is to make the Build form actually drive synthesis, scope capabilities per account, and surface the evidence/metadata the backend already persists.

**Baltor** — A governed context product where a tenant ingests real sources into tiered, provenance-anchored corpora; a six-stage engine reconciles/hardens/optimizes them against live authoritative sources; a serve console returns verified, cited chunks (holding stale/contradicted content out) with receipts; and compliance artifacts (AIBOM, EU AI Act dossier, C2PA, fidelity record) are emitted on demand and signed. Today it is a fixture prototype; the north star is to replace every fixture in `ce-store.jsx` with real ingest/engine/serve/verify/artifact services behind `/api/baltor/*` seams, add an auth gate, and scope all data to the authenticated tenant.

---

## (B) Teleon capability experience (owner-requested)

Each richer feature with Purpose / Problem / PMF / Exists today? / Gap. Grounded in the Teleon trace's north-star (a–f) findings.

| Feature | Purpose | Problem solved | PMF | Exists today? | Gap |
|---|---|---|---|---|---|
| **(a) Generated-code review** | View the code a capability synthesized | Buyers won't trust an opaque "promoted" badge; they must read what runs | Compliance/eng leads who must review before deploy | **No UI.** Runtime uses pure-Python impls; no view of generated code | Build never synthesizes typed purpose (`teleon-main.jsx:311`, `run()` called with no id), so there's nothing to show; need a code-render panel fed from the compiled unit |
| **(b) GitHub/GitLab-style code + forks + versions + history browser** | Browse versions, diffs, forks of a capability | Teams need lineage and the ability to branch a capability safely | Platform teams standardizing capabilities | **Partial backend, no UI.** Runtime keeps a version number + `runs.jsonl` event log; **no forks, no history UI** | Build a version/history/diff browser; add a fork concept (backend has neither forks nor a diff surface) |
| **(c) License / guardrail / preference selection** | Choose allowable licenses, guardrails, prefs that bind the build | Orgs must enforce policy (license, auto-rollback) at synthesis time | Regulated buyers; procurement | **No.** The only toggles (Settings, criteria) are no-ops; criteria toggles ignored | Criteria toggles cosmetic (never sent); Settings `onToggle={() => {}}`; "Auto-rollback" ON changes nothing in the gate — wire toggles into the run request + runtime gate |
| **(d) Export of code / capability / diagram** | Export the capability as code, a portable unit, or a diagram | Customers need to take artifacts to deploy/audit elsewhere | Buyers needing AIBOM/portability | **No.** Audit claims "exportable" but nothing exports | No export path; backend compiled unit exists (`exec_target` fly_machine/k8s_job/local_process) but no UI export action |
| **(e) Capability runtime metadata (trigger, runtime, inputs/outputs, cloud-function vs docker, language)** | Show how/where a capability runs | Operators must know trigger, I/O contract, and execution target before relying on it | DevOps / platform buyers | **Partial backend, not surfaced.** Compiled unit carries `exec_target` (fly_machine/k8s_job/local_process), purpose/criteria/examples, expected I/O | UI shows only name/status/score/version — no trigger/runtime/inputs-outputs/cloud-vs-docker/language surface |
| **(f) Component bill-of-materials / diagram** | Show which registry components a capability used/edited/generated | Reuse-first governance ("don't reinvent"); supply-chain audit | Governance/security buyers | **No.** Runtime uses pure-Python impls, not registry components; nothing surfaced | No BOM, no diagram; /registry page is static prose and never queries the `/registry` seam |

---

## (C) Prioritized remediation backlog (highest user impact first)

Ordering principle: (1) trust-breaking demo-data leaking into brand-new accounts, (2) account flows a real user is blocked on, (3) broken/dead handlers, (4) the capability-experience build-out. Each item names the file to change.

**P0 — Demo data leaking into every new account (trust-breaking; do first)**

1. **Teleon dashboard fake activity/stats/plan for zero-run accounts** — `activity()` null → "$249.00 invoice paid" / "usury-rate finder promoted 0.96"; stats fallback 38 promotions; plan mini always `{Team,62}`. Fix `_repos/teleon/frontend/teleon-main.jsx:396-403` to render real empty states (no fixtures when runtime up / account new).
2. **API-key fixtures shown to all accounts** — 3 fake `sk_live_9f2c / sk_live_3b71 / sk_test_a1f0` always prepended. Remove fixtures and call `listKeys()` on mount. Fix `kit/oh-site.jsx:652-656` (+ wire `oh-identity.js:61` listKeys via a `useEffect`; backend `identity_local_service.py:446-453` already exists).
3. **Audit log shows fiction over a real ledger** — fixture receipts (`oh-site.jsx:775-781`) while `audit-events.jsonl` (255KB real) exists. Add a read endpoint to `scripts/identity_local_service.py` (and `teleon_local_runtime.py` receipts for /audit), add client method + `useEffect`, drop fixtures.
4. **Team / Billing / Usage / Settings fixtures everywhere** — Ada Lovelace / Turing / Hopper, Team $249 invoices, "4,120 Runs", "ada@company.com". Replace with real-or-empty: `kit/oh-site.jsx:737-742, 515-550`; props at `teleon-main.jsx:415-428`; Baltor `ce-app.jsx:501-518, 593-641` + `ce-store.jsx` (CORPORA/CONFLICTS/COMMONS/etc.). For Baltor, removing fixtures also requires the backends below.
5. **Baltor renders one tenant's data unauthenticated** — whole workspace shows "Acme · Compliance / Pro" with no login. Add the identity seam + an auth gate in `ce-main.jsx:31-41` / `ce-shell.jsx:121`.

**P1 — Account flows a real user is blocked on**

6. **Password reset is pure theater (no recovery possible)** — add a one-time-token reset endpoint to `scripts/identity_local_service.py`, a client method in `oh-identity.js` (none exists), and replace the local `setSent(true)` at `oh-site.jsx:417-431`.
7. **/dashboard is not gated on session validate** — an unauthenticated user reaches the fixture console. Add a route guard calling `OHIdentity.validate(realm)` (`oh-identity.js:56-59`; backend `:430-436` exists) before rendering account routes.
8. **Signup Name dropped** — `oh-site.jsx:439` collects a display name the register call never sends. Extend the register payload + `realm.register` (`identity_local_service.py:391-402`) to persist it.
9. **Onboarding checklist disconnected** — drive real `onboarding_steps` per step via `/onboard` (`identity_local_service.py:403-407`) from `oh-site.jsx:902-923`; stop signup auto-completing all steps so progress is real.

**P2 — Broken / dead handlers (controls that lie about working)**

10. **Baltor Download bundle / Download tier / Emit artifact** — dead `<button>`s `ce-app.jsx:149, 170, 209`; wire to an artifact service (signed bundle / tier export / compliance artifact).
11. **Baltor "Verify by hash" (the central trust claim) and "Rotate keys"** — no onClick `ce-app.jsx:458, 489`; wire to an attestation check and a real token rotate.
12. **Fixture-row "Revoke" links inert** — `oh-site.jsx` revoke only on `k.real`; once #2 drops fixtures this resolves, but verify no dead Revoke remains.
13. **Identity service-connection console missing** — backend `service_handshake` (`identity_local_service.py:264-387`) is wired and proof-tested but has no UI; add an operator page to mint/list/verify/revoke service connections.

**P3 — Baltor core write paths (make the product real)**

14. **Ingest** — replace the `setTimeout` walk (`ce-app.jsx:51-124`) with `POST /api/baltor/ingest`; real parse/chunk/fingerprint/tiers/persist; "Open corpus" opens the new id.
15. **Engine pipeline run** — replace RAF fill (`ce-pipeline.jsx:81-100`) with a real engine service streaming per-stage counts + run records/receipts.
16. **Serve console** — replace MOCK_CHUNKS (`ce-app.jsx:228-232, 271`) with a real retrieve→rerank→freshness→verify→cite call returning a receipt.
17. **Verify/reconciliation HITL** — replace the local `resolved` map (`ce-app.jsx:316-318`) with a PATCH to a reconciliation service that updates/quarantines chunks + emits a receipt; feed REG_CHANGES/WATCHED from a live CDC.

**P4 — Teleon capability experience (owner a–f)**

18. **Make Build actually synthesize the typed purpose** — `run()` is called with no id (`teleon-main.jsx:311`), always re-running global `cap-dates`; send the textarea + criteria toggles; remove the setTimeout lifecycle theater (`:296-300`) and reflect the real run phases.
19. **Per-account capability scoping** — `capabilities.json` is global, open-read (`teleon_local_runtime.py:294-301, 737-738`); scope reads by session so a new account starts empty.
20. **Evidence page wiring** — call `GET /api/teleon/teleon/evidence?run_id=…` (`teleon_local_runtime.py:752-753, 684-687`) with a real id from the capabilities row link (`teleon-main.jsx:283`); render version-by-version train/holdout receipts.
21. **Capability metadata + code + history + BOM + export** — surface compiled-unit metadata (`exec_target`, I/O, language) and add the generated-code view, version/fork/history browser, guardrail/license/preference selection (wire the no-op toggles `teleon-main.jsx:426`), export, and a component bill-of-materials/diagram (the /registry page `teleon-main.jsx:417` never queries the `/registry` seam).
