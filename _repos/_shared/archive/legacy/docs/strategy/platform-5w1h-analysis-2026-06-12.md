# Platform 5W1H analysis — surfaces, functionality, pipelines (2026-06-12)

A who/what/where/when/why/how pass over every surface, function, and pipeline, each
with **where we can improve**. Grounded in: the surface registry
(`architecture/demo_surface_registry.json`), the 29-journey recording
(`artifacts/e2e/reports/user-journeys.json` — real friction counts), the service
registry, and direct code reads. Improvement items are tagged by effort (S/M/L) and
rolled into a prioritized backlog at the end.

Legend — **W5H** = Who · What · Where · When · Why · How. Improvements cite real
evidence, not aspiration.

---

## PART A — SURFACES (what a user/agent touches)

### A1. The 9 static brand sites (parent, Teleon, Baltor, 6 Open*Hubs)

- **Who:** prospects, demo reviewers, the owner pitching. **What:** marketing/launch
  pages stating each brand's thesis. **Where:** `dist/sites/…`, ports 9100–9107, served
  by `serve_portfolio_sites.py`. **When:** always-on preview; the front door of every
  demo. **Why:** the proof-first GTM surface — "AI, done right." **How:** static HTML +
  the branded-house design system (Hanken Grotesk / IBM Plex Mono).
- **Improve (HIGHEST-FREQUENCY GAP, 21× in the recording):** the journeys flag *"A REAL
  account on this site's own realm"* + *"email field not present where expected"* on every
  open-hub *static* site. These sites are marketing pages with **no auth kit at all** — the
  recorder (which gates app chapters behind a real sign-up) expects a sign-up the static
  sites don't offer. Two honest readings: either (a) the open-hub sites are intentionally
  marketing-only and the recorder's expectation should be relaxed for them, or (b) they
  should get the shared `OhAuth` kit + their realm. The realms exist
  (`/api/identity/realms`); the apps (harness-hub/baltor/teleon) already wire real auth —
  the static hubs don't. **(M)** Decide per-hub: mount the auth kit on the hubs meant to
  convert, leave the rest marketing-only and tag them so the recorder stops flagging them.

### A2. The 4 product apps

| App | Port | What it does | Honest state |
|---|---|---|---|
| OpenHarnessHub SPA | 8000 | ~30 routes: build→results, pipelines/components catalog, foundry/improve/registry/settings/admin/workers workspace, flow/run trace | real auth to identity service (`/api/identity/openharnesshub/*`, localStorage session); listings are mock; source-search rows "not implemented" honestly (`proto-ops.jsx:137`) |
| Baltor app | 8001 | corpora library, ingest sources, corpus detail `/c/<id>`, serve/verify/governance/billing workspace | real UI + shared `OhAuth` kit on its OWN `baltor` realm; one hero card pinned, not fully clickable |
| Teleon app | 8003 | capabilities list, runs/build, evidence, API keys, team/audit; lifecycle rail | lifecycle rail is static narrative; hero card is a closed mock; app routes exist, thin proto |
| Context-Is-Everything | 8002 | single-page family/thesis site, no SPA routes, no auth | pure presentation (founding-thesis legacy path) |

- **Who:** developers (harness-hub), compliance/applied buyers (baltor), staff/agents
  (teleon). **When:** post-sign-up (the journeys gate app chapters behind a real
  sign-up). **Why/How:** each app is the door to one product layer; same design system,
  separate realms (no SSO, owner-locked); auth shares one kit, realm derived from brand.
- **Improve (corrected by code read — most "broken" frictions actually work; the real bug
  is subtler):**
  (1) **THE REAL AUTH BUG — silent no-session fallback:** when the identity service is
  down, `OhAuth.submitAuth()` quietly redirects to `/dashboard` with NO session created and
  NO "this is a preview, not persisted" message (`kit/oh-site.jsx:307-311`). A user thinks
  they signed up; nothing was saved. **(S)** show an explicit preview banner on the fallback
  path. Highest-value app fix.
  (2) **Settings reachable in-app but not from marketing chrome** — once logged out it's
  unreachable; the in-app link is a de-emphasized ~11px footer link
  (`kit/oh-site.jsx:250`). **(S)** add Settings to the marketing nav + raise the footer link.
  (3) **Email field present in `/signin` `/signup` but missing from the marketing top-nav
  CTA** (it's a button to `/signin`, not an inline form) (`proto-main.jsx:81`). **(S)**
  optional inline email capture in the navbar.
  (4) **OAuth (Google/GitHub) buttons render disabled** ("Owner-gated seam —
  CredentialProviderPort", `kit/oh-site.jsx:346`) and **password reset is a UI-only
  placeholder** (no email send). **(M)** wire the real transactional-email path (the mailbox
  service at :9428 already exists) to make reset + verify real.
  (5) **teleon:** promote `purpose_tasks` candidate→live against the real runtime (`:9430`),
  and make the hero card clickable. **(M)**
  (6) **harness-hub source-search:** the "not implemented" rows now have real backends (the
  23-module retrieval family) — **(M)** wire "Ingest & gate" to the real intake path, not a toast.

### A3. Service-plane services (the machine room)

- **Who:** other services + the apps (server-to-server). **What/Where/Port:** identity
  9410, mailbox 9428, registry/openhub-projection 9423, events 9420, Teleon runtime 9430,
  Baltor backend 9301, control tower 9000. **When:** always-on local; the recordable
  seams. **Why:** the planes the apps consume. **How:** small Python services, SQLite
  local / Postgres+Redis in cloud by env; all 6 recordable seams answer 200 over tunnels
  (verified this session).
- **Improve:** 6 registry services are `status: planned` with **no start_command**
  (ab-test 9421, service-account 9422, mcp-registry 9424, llm-plane 9425, receipt 9426,
  state 9427). **(M)** Either implement the planned six or mark them out of the active
  plane so the family count is honest. Receipt (9426) and state (9427) are the most
  load-bearing for the assurance thesis — prioritize those.

### A4. Demos, dashboards, registries, internal tools

- **CFPB offline e2e** (`baltor.cfpb_offline_demo`) — the PROVEN proof point (answer = "10
  business days", FAQ "30 days" held out, receipt + handles). **Who:** every buyer demo.
  **Improve:** it's the single best asset — **(M)** record a narrated video now that the
  recording gate is GO (the one remaining item from the backbone memory).
- **4 open-hub registries + 2 internal tools** are `candidate`/`internal_only` —
  correctly not shown as live. **Improve:** the registry APIs (`:9500/api/open*`) are the
  natural home for the repo-intel candidates (markitdown, docling, etc. intaken this
  session) — **(L)** stand up one registry read API for real.

---

## PART B — FUNCTIONALITY (what the platform can do)

### B1. The context-layer processor families (56 modules, ALL self-tested this session)

cache 4 · memory 6 · retrieval 23 · compression 2 · clinical 8 · deliver 10 · connectors 3.

- **Who:** the consumption runtime + any pipeline assembling context. **What:** the
  swappable method-components of the governed context pipeline (retrieve → rerank →
  compress → place → cache → deliver; memory recall/reflect/belief; clinical decision-
  support; governed connectors). **Where:** `scripts/processors/<family>/`. **When:**
  invoked per context-serving step. **Why:** the negative-space capability lift — what
  base models lack. **How:** deterministic, injected seams, honest fallbacks, lossless,
  `serves_truth` pinned.
- **Improve (THE load-bearing gap):** these 56 are resolvable catalog callables but the
  **live runtime (`scripts/runtime/builtin_processors.py`) invokes a separate hand-wired
  CFPB-specific set** (`ContextPackBuilder`, `DeterministicVectorizer`…). The 56 are not
  yet on the live consumption path. **(L)** Build a processor registry that maps
  `process_kind → the catalog callable` so the runtime dispatches the real families. This
  is the bridge between "179 callables resolve" and "the product uses them."

### B2. Auth (realms + shared kit)

- **Who:** end users per product. **What:** separate login/onboarding per realm
  (aidoneright/baltor/…), NO SSO, one shared kit. **Where:** `src/openharnesshub/auth_kit`
  + identity service 9410. **When:** sign-up gates every app. **Why:** owner-locked
  independent realms. **How:** realm config with `onboarding_steps` (verify_identifier →
  accept_terms → set_workspace).
- **Improve:** the realms + per-product accounts are REAL (apps wire them), but (a) static
  hub sites don't surface auth at all (Part A1), and (b) the **silent no-session fallback**
  (Part A2.1) makes a down-service look like a successful sign-up. The backend is ahead of
  the frontend — **(S)** fix the silent fallback first, then decide the hub-auth question.

### B3. Inference gateway / OIPS

- **Who:** every model call. **What:** provider-neutral routing + cheapest-capable model
  selection + portable receipts; LLM output never truth. **Where:** `src/teleon/inference/`
  (oips, model_efficiency, adapters, receipts). **When:** per capability/eval/generation
  call. **Why:** provider neutrality is the structural edge OpenAI/Ona can't match.
  **How:** 7-layer preference inheritance (global→product→tenant→env→object-type→instance→call)
  → numeric provider selection (tier/policy/health/secret) → cost/latency ranking → receipt
  (`is_truth: False` always, plane-stamped, drops api_key/prompt). **Improve:** (1) **(M)**
  add Mistral + OpenRouter + GitHub-Models lanes as first-class + a live smoke per lane
  (owner's keys ready, seams exist). (2) **external leaderboards defined but never fed** —
  `EXTERNAL_SIGNAL_WEIGHT` exists in `model_efficiency.py:40` but nothing ingests
  ClawWork/HKUDS data, so cheapest-capable is cost/latency only. **(M)** wire the external
  signal. (3) **no quality dimension** — `rank_models()` accepts a quality dict but the
  foundry measures lift per *capability*, not per *model*, so a fast-cheap model that
  produces low-quality output can win. **(L)** annotate model quality so the ranking trades
  cost against output quality, not just latency.

### B4. Governance — verification + promotion gates

- **Who:** the candidate→active boundary. **What:** the gates that decide what becomes
  tenant-visible (`scripts/runtime/verification_gate.py`, rule/parallel-path promotion
  gates, sandbox gate). **When:** before any promotion. **Why:** governance IS the
  external moat. **How:** warrant-checked, two-axis lift, lossless. **Improve:** **(M)**
  surface the gate verdict in the app UI (`check_pipeline_verification_ui.py` exists as a
  check but the live UI affordance is thin) so a reviewer SEES "proposed → verified →
  promoted" with the receipt.

### B5. Monitoring — heartbeat / resolution flywheel

- **Who:** the always-on control plane. **What:** ping every surface → classify
  transient/persistent → propose (never auto-act) restart/reheal/escalate. **Where:**
  `src/teleon/monitoring/flywheel.py`. **When:** every tick. **Why:** recordable-readiness
  + self-healing without unbounded autonomy. **How:** `PERSISTENT_AFTER` / `ESCALATE_AFTER`
  thresholds, propose-only. **Improve:** **(S)** the planned receipt service (9426) would
  let proposals carry a durable receipt; wire once 9426 exists.

---

## PART C — PIPELINES (how work flows)

### C1. Foundry daily batch

- **Who:** the factory. **What:** generate component candidates + showcase pipelines; emit
  the row families (source_record → normalized_object → canonical_entity → … →
  object_embedding → index_record → review_ticket). **Where:** `scripts/foundry/` (17
  stage modules; `make test` self-tests each). **When:** per `make foundry` run. **Why:**
  the database-backed registry substrate. **How:** 8 stages (gaps→sources→construct→
  standardize→novelty→measure→gate→stage_load), fully real offline; CULL never minted, only
  PROMOTED+REVIEW rows persist; PROMOTED → `approval_status: pending_human`. **Improve:**
  (1) **measurement is offline-capped** (`measure.py`): scores come from *recorded* eval
  answers; without live BareModel+PipelineRunner+Judge adapters, new gaps are never measured
  and route to REVIEW. **(M)** wire live scorers (now unblocked by the owner's Mistral/Ollama
  keys) so the two-axis gate gets real lift data. (2) **novelty dedup is content-only**
  (`novelty.py`): dedup by source-URL + payload-hash, no semantic clustering — a reformulation
  across sources is dropped as a clone while two different facts from one source both promote.
  **(M)** add a semantic sameness check (the `retrieval/simhash_dedupe` + embeddings now exist).

### C2. Ingestion (feed / freshness / health)

- **Who:** the corpus acquisition lane. **What:** feed registered sources → govern →
  CDC-poll for changes → reingest; health-check reachability. **Where:** `scripts/ingest/`
  (feed, freshness, health, source_adapters, parser_provider). **When:** `make ingest` /
  `ingest-loop` sidecar. **Why:** Verified+Current+Provable governed data. **How:**
  **OFAC SDN is REAL live** (positional-CSV parser in `sanctions_feed_live.py`);
  ecFR/Federal-Register are fixtures; BIS/EU sanctions declared but raise
  `NotImplementedError`. **Improve:** (1) **parser seams incomplete** — Docling lazy-loaded,
  PDF/HTML behind `UnavailableParserAdapter` (honest consumable=False, never fake), BIS/EU
  not wired. **(M)** wire docling (intaken this session) + the BIS/EU parsers. (2)
  **health-check ≠ promotion gate** — fed rows are staging-only; no downstream measure/gate
  job to reach tenant-visible (`feed.py`, `health.py`). **(M)** add the
  staging→measure→gate→promote job to the Makefile so ingested facts can actually promote.

### C3. Context-serving / consumption runtime

- **Who:** the product's hot path. **What:** assemble a governed context pack and serve it
  (the CFPB→consumption demo proves it end-to-end). **Where:** `scripts/runtime/`
  (context, consumption, builtin_processors, verification_gate). **When:** per query/turn.
  **Why:** the consumption context layer is the TAM. **How:** processors → artifacts →
  verification gate → consumption. **Improve:** **(L)** this is where the context-
  efficiency thread lands: today every turn re-streams the pack; wire
  `usage_gated_compress` (built this session) + `cache_prompt_prefix` + the page-in/out of
  `memory_agentic_hierarchy` so the runtime serves predictable context by handle and pays
  full cost only on a prediction miss. See `docs/concepts/prediction-error-gated-context.md`.

### C4. Capability backbone (capability → eval → gate → compile → register → launch)

- **Who:** Teleon's runtime SaaS. **What:** describe a capability + eval → build → gate
  (ungameable) → promote → auto-compile → register (rollback-able) → launch on Fly.
  **Where:** `src/teleon/compiler/`, the promotion bridge, `teleon_local_runtime.py`, the
  Machines runner. **When:** on promotion (zero-op, opt-in). **Why:** the receipt-backed
  CapabilityTask agents call instead of burning tokens. **How:** local runtime executes
  examples → holdout pass-rate ≥ PROMOTE_AT (0.90) → deterministic compile → registry
  (rollback_target) → optional Fly launch. **Improve:** (1) **only `local_function_target` is
  ACTIVE** — the other 6 binding targets (Nitric/Score/Temporal/Knative/KEDA/Kratix) are
  never-executed candidates that degrade to `BindingUnavailableResult`
  (`capability_binding.py:38-67`). **(M)** pick one and wire its policy/pricebook so a real
  non-local backend exists. (2) **launch is Fly-specific** — k8s_job/local_process emitters
  exist but have no launcher, and the zero-op thread needs a Fly token. **(M, owner-gated)**
  add a kubectl launcher for portability; the named-suite registry behind `benchmark_ref` is
  the other open seam.

### C5. Deploy plane

- **Who:** the agent (after owner billing). **What:** topology → fly configs + worker
  controller + seams → preflight GO → deploy. **Where:** `architecture/deploy_topology.json`,
  `scripts/deploy/`. **When:** on `fly auth login`. **Why:** cheap, agent-automatable,
  separable. **How:** single-source generator, preflight GO 9/9 (verified this session).
  **Improve:** **(S)** add the Mistral/OpenRouter/Ollama-Cloud secret names to the
  per-app `fly secrets` list in the runbook so the model lanes deploy with the plane.

---

## PART D — Cross-cutting: the context-efficiency thread

The active research thread (`prediction-error-gated-context.md`) touches every pipeline:
cache (don't re-send) → compress (send less) → handle+rehydrate (send by reference) →
persist (distill out of the loop). The biggest wins are at the ends (caching, persistence),
not the middle (compression). The **cohort policy selector** (classify a tenant's usage
shape → pick the compression curve) is the genuinely new, unbuilt capability that answers
"based on consumer behavior."

---

## PART E — Prioritized improvement backlog

Ranked by (value × inverse effort), value weighted toward proof-points and the active thread.

1. **Fix the silent no-session auth fallback** (A2.1) — a down identity service currently
   looks like a successful sign-up; add a preview banner. Fastest, highest-trust fix. **S**
2. **Bridge the 56 catalog processors into the live runtime** (B1/C3) — turns "callables
   resolve" into "the product uses them"; unlocks the context-efficiency work. **L**
3. **Wire live model scorers into foundry `measure`** (C1) — now unblocked by the owner's
   Mistral/Ollama keys; gives the two-axis gate REAL lift data instead of recorded answers. **M**
4. **Add Mistral/OpenRouter/Ollama-Cloud lanes + per-lane smoke** (B3) — owner's keys ready,
   seams exist; also the prerequisite for #3. **M**
5. **Record the CFPB proof video** (A4) — recording gate is GO; best sales asset. **M**
6. **Marketing-nav fixes** — Settings link + email CTA + raise the footer link (A2.2/A2.3). **S**
7. **One real parser backend (docling) + staging→gate job on the ingest seam** (C2). **M**
8. **Wire the external-signal + quality dimension into OIPS ranking** (B3) — cheapest-capable
   is cost/latency-only today; a fast-cheap-but-low-quality model can win. **M→L**
9. **Cohort policy selector** (D) — the new "consumer behavior" capability. **L**
10. **Semantic novelty dedup in foundry** (C1) + **gate verdicts/receipts in the app UI** (B4)
    + **receipt (9426)/state (9427) services** (A3/B5). **M each**

Items 1, 5, 6 are the fastest visible wins. Item 2 is the deepest unlock. Items 3+4 are the
"now that keys exist" wins. Item 9 is the most novel. Deploy/launch (C4/C5) are owner-gated
on the Fly account. **Net theme: the backend consistently runs ahead of (a) the frontend that
should surface it and (b) the live model lanes that would give it real data — most top items
close one of those two gaps.**
