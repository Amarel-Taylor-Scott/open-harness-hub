# Teleon — edges view (connections, seams, and compatibility contracts)

**Purpose.** This is the interface contract for **Teleon** as it moves toward being managed
separately: what it consumes from the other components, what it exposes to them, the same-origin
seams, and the invariants that MUST hold so a separate session cannot break the portfolio. The
standalone "what Teleon is" brief is `_repos/teleon/context/blackbox.md`.

**Grounding.** Every edge and contract below is a summary of, and a link to, an existing repo doc
or machine source. The dependency direction is a **law enforced by a proof**, not prose — if this
file and the cited source disagree, the source wins.

Primary sources synthesized here:

- `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` — the machine source of the dependency law + migration status (proof: `_repos/shared-backend-components/scripts/check_portfolio_dependency_law.py`).
- `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` — the Teleon API surface, hosting topology, separability levers.
- `_repos/_shared/ARCHITECTURE-MAP.md` — the six-component map + the seam table.
- `_repos/shared-backend-components/docs/INTEGRATION-BIBLE.md` §1–§2 — the frontend↔backend seam contract.
- `_repos/teleon/backend/src/teleon/README.md` + `_repos/teleon/backend/src/teleon/agent_gateway/gateway.py` — the package boundary + the agent seam.

---

## 1. The dependency law (honor it — enforced, not optional)

```
Baltor ───────────► Teleon ───────────► OpenHubForAI
(applied product)   (runtime SaaS)      (open ecosystem + spec)
```

- **Baltor depends on Teleon** — it calls the Teleon API as tenant `baltor-internal`.
- **Teleon MAY consume OpenHubForAI** artifacts (harnesses, templates, skills, the open CapabilityTask spec).
- **OpenHubForAI depends on neither.**

**Forbidden edges (the build fails on any of these import directions):**

- **Teleon MUST NEVER import Baltor (`src.baltor.*`)** — Teleon is reusable infrastructure, not a Baltor feature. This is the single most important invariant for managing Teleon separately.
- **OpenHubForAI must never import Baltor or Teleon** — the open ecosystem/spec stays neutral.

Branch on the layer + edge, never on a brand display name. `scripts` is tooling, not a brand layer,
so a Teleon module importing `scripts.runtime.schema_validator` does NOT create a `teleon → baltor`
edge.
Source: `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` (`law`, `forbidden_edges`, `layers`); `_repos/teleon/backend/src/teleon/README.md` ("Architectural law"); `_repos/_shared/ARCHITECTURE-MAP.md` ("The architectural law").

## 2. What Teleon CONSUMES (inbound dependencies it is allowed to have)

- **OpenHubForAI artifacts** — harnesses, task templates, skills, conformance tests, and the
  **open CapabilityTask spec (CTS)** that Teleon is the reference implementation of. Teleon
  consumes OHH; OHH never consumes Teleon.
  Source: `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` → `layers.teleon.may_depend_on = ["openhubforai"]`; portfolio doc ("Teleon implements the open CapabilityTask Spec").
- **The backend registry / primitive substrate** — the database-backed component registry, the
  seven-primitive model, Knowledge Corpus / context packs, and imported workflow/skill/framework
  candidates that feed Stage 3 (BUILD). All imported material enters **as a candidate behind a
  port** (`serves_truth=false`) and must pass the gate.
  Source: `_repos/shared-backend-components/docs/strategy/teleon-self-improving-runtime-vision.md` §C; `_repos/_shared/ARCHITECTURE-MAP.md` (component 6, Backend).
- **Reference context (from OpenHubForAI, governed by Baltor's rail)** — "reference context is
  not served truth"; Teleon may run over it but does not adjudicate its truth.
  Source: portfolio doc ("Relationship" + method-hub boundary).

Teleon otherwise imports only the standard library within `_repos/teleon/backend/src/teleon/**` (the OIPS/receipt/compiler
modules are SDK-free and offline at load).
Source: `_repos/teleon/backend/src/teleon/inference/oips.py`, `_repos/teleon/backend/src/teleon/agent_gateway/gateway.py` docstrings ("no external SDK import, no network").

## 3. What Teleon EXPOSES (outbound interfaces others call)

**3.1 The Teleon API surface — the boundary Baltor (and any tenant) calls:**

```
POST /purpose-tasks                          GET  /purpose-tasks            GET /purpose-tasks/{id}
POST /purpose-tasks/{id}/run                 POST /purpose-tasks/{id}/evaluate
POST /purpose-tasks/{id}/run-side-by-side    POST /purpose-tasks/{id}/promote
POST /purpose-tasks/{id}/rollback            POST /purpose-tasks/{id}/request-boundary-approval
GET  /purpose-tasks/{id}/evidence            GET  /purpose-tasks/{id}/customer-assurance
```

`promote` opens a Promotion + runs the policy engine; **it never deploys directly**. This versioned
contract is the ONLY coupling between Teleon and Baltor.
Source: `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("Teleon API surface").

**3.2 The Agent Capability Gateway — the seam an AI agent calls (agents are customers).** LIST a
small stable catalog → DESCRIBE a capability → QUOTE cost/latency/runtime-path-plan → RUN (writes a
receipt) → REQUEST a boundary expansion (always `pending_human_approval`, `auto_applied=False`).
Deterministic-first down the token ladder; an agent can never force LLM fallback, read a secret
value (refs are `env://` strings), call a forbidden tool, run outside its allow-list, weaken
success criteria, or self-expand its boundary; `serves_truth` is pinned false on every result.
Source: `_repos/teleon/backend/src/teleon/agent_gateway/gateway.py` (module docstring "THE LAW").

**3.3 Runtime artifacts** — the **CompiledRuntimeUnit** (`_repos/shared-backend-components/schemas/runtime/CompiledRuntimeUnit.schema.json`,
emitted as Fly Machine / K8s Job / local-process shapes), **ModelInvocationReceipts** / evidence
ledger rows (`is_truth:false`), and the **runtime-class binding** decision. Every output is
**evidence the caller receives, not a fact it can re-sell** — Baltor's rail governs truth; the
gateway never emits the `served` use-level.
Source: `_repos/teleon/backend/src/teleon/compiler/emit.py`; `_repos/teleon/backend/src/teleon/inference/{oips,receipts}.py`; gateway docstring.

## 4. The seams (same-origin frontend ↔ backend contract)

A frontend never hardcodes a backend host; it calls a same-origin **seam path** the showcase
rewrites to the real backend (local service registry by default, `OH_SEAM_*_BASE` env in cloud).
The Teleon-relevant seams:

| Frontend calls (same origin) | Backend service | Local registry id (port) | Cloud override env |
|---|---|---|---|
| `/api/teleon/...` | Teleon runtime | `teleon_local_runtime` (9430) | `OH_SEAM_TELEON_RUNTIME_BASE` |
| `/api/observer/...` | AIDevObserver session review (built on `_repos/teleon/backend/src/teleon/observer`) | `observer_runtime` (9431) | `OH_SEAM_OBSERVER_BASE` |
| `/registry/...` | registry / catalog projection (the substrate Teleon consumes) | `local_openhubforai_projection_api` (9423) | `OH_SEAM_REGISTRY_BASE` |
| `/api/identity/...` | shared auth / identity | `local_auth_service` (9410) | `OH_SEAM_IDENTITY_BASE` |

A new frontend↔backend integration is always **a service-plane service + a seam + a
`fetch('/api/<x>/...')`** — never a hardcoded host.
Source: `_repos/_shared/ARCHITECTURE-MAP.md` ("The seams"); `_repos/shared-backend-components/docs/INTEGRATION-BIBLE.md` §1–§2 (source of truth: the seam table in `_repos/shared-backend-components/scripts/showcase/server.py`).

## 5. Relationship to each of the other five + `_shared`

- **AI Done Right (parent brand / holding company)** — Teleon is one of its products. The parent
  owns no runtime code and no customer data and sponsors OpenHubForAI; it does not sit in Teleon's
  import path.
  Source: `_repos/_shared/ARCHITECTURE-MAP.md` (component 1); portfolio doc ("Holding company").
- **Baltor (applied product, tenant `baltor-internal`)** — Baltor calls the §3.1 API as a tenant;
  **Baltor → Teleon, never the reverse.** Baltor governs TRUTH, Teleon governs EFFICIENCY — different
  objects. Baltor holds re-export **shims** for the concepts extracted out of it (see §6).
  Source: portfolio doc ("Moat split", "What moves out of Baltor → Teleon"); dependency-law file.
- **OpenHubForAI (open ecosystem + spec)** — Teleon consumes its artifacts and is the reference
  implementation of the open CapabilityTask spec; the spec is stewarded by OHH for neutrality.
  Never `openhubforai → teleon`.
  Source: portfolio doc ("Relationship"); dependency-law file.
- **AIDevObserver (AI-usage layer)** — currently **built on `_repos/teleon/backend/src/teleon/observer/`** (router,
  review, capture, session_store) + `_repos/teleon/backend/src/teleon/economics/`, reached over `/api/observer/`. This is
  a real coupling detail: Observer code lives inside the Teleon package today while being grown
  toward a standalone product — changes to `_repos/teleon/backend/src/teleon/observer/**` touch that surface.
  Source: `_repos/_shared/ARCHITECTURE-MAP.md` (component 5); `_repos/shared-backend-components/architecture/substrate_layers.json` → `layers[ai_waste_engine]`.
- **Backend (registry / primitives / service-plane substrate)** — Teleon consumes it as the reuse
  substrate and reaches it over `/registry/`; it must not be reached by a hardcoded host.
  Source: `_repos/_shared/ARCHITECTURE-MAP.md` (component 6).
- **`_shared`** — the cross-component contracts Teleon obeys: the eight component STANDARDS
  (no-magic-values, deterministic naming both planes, change-verification warrant, codegraph audit,
  lossless distillation, archive-never-delete, promotion boundary), the GLOSSARY, and the
  ARCHITECTURE-MAP. Notably, generated ids in Teleon are minted ONLY by
  `src.teleon.experiments.ids` (`canonical_id`), and version lives in `schema_version` metadata,
  never in a name.
  Source: `_repos/_shared/STANDARDS.md` (laws 1–8, esp. §3 DATA-plane naming).

## 6. Migration status (Baltor → Teleon extraction — COMPLETE, shims remain)

Generic runtime concepts were extracted `src/baltor/` → `_repos/teleon/backend/src/teleon/` **incrementally and
losslessly** (move a module + leave a Baltor re-export shim so callers and proofs stay green — never
big-bang). The dependency-law file records the extraction as **COMPLETE** across four layers:

1. **Execution layer** → `_repos/teleon/backend/src/teleon/runtime/**` (ports + backend selector + execution providers).
2. **Parallel-Path Engine** → `_repos/teleon/backend/src/teleon/experiments/**` (ids, parallel_paths, path_comparator, path_promotion, path_costing, path_rollback, boundary_approval).
3. **PurposeTask** → `_repos/teleon/backend/src/teleon/purpose_tasks/**` (controller + runtime binding + adaptation ladder + projections).
4. **Fleet/execution substrate** → `_repos/teleon/backend/src/teleon/workers/**` (`fleet_ledger`, `durable_fleet_ledger`, emulators, dispatch); plus `src/baltor/teleon_client` so Baltor calls Teleon as a tenant.

Consequences for a separate manager: Baltor still imports many of these names, but only through
**re-export shims** — the real code is Teleon's. Two pre-move traps are recorded: pre-grep must
catch **lazy (inside-function) absolute imports** and **explicit underscore-private imports**
(`from <mod> import _NAME`), both of which a top-level grep misses and both of which can silently
recreate a `teleon → baltor` edge after a move. One known stale-header contradiction lingers
(`_repos/teleon/backend/src/teleon/workers/durable_fleet_ledger.py` line 1 still names `src.baltor…`), functionally fine
but flagged to reconcile.
Source: `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` → `migration_status` (`extracted_so_far`, `lessons`); `_repos/shared-backend-components/docs/strategy/teleon-self-improving-runtime-vision.md` §D-7.

## 7. The compatibility contracts to PRESERVE (do not break these)

When Teleon is managed by a separate session, these invariants keep the portfolio compatible:

1. **No forbidden import edge** — never `teleon → baltor`; keep Teleon SDK-free/offline at load in the pure modules. Enforced by `_repos/shared-backend-components/scripts/check_portfolio_dependency_law.py`.
2. **The versioned API is the only coupling** — Baltor integrates via §3.1 + events, never a private cross-boundary import.
3. **No shared database** — Teleon owns its runtime/evidence store; Baltor owns customer data; integrate via API + events, no cross-DB joins.
4. **No shared code except the open spec / published OHH packages.**
5. **Separate identity / billing / IaC** — either product redeploys independently (co-located for latency, cleanly separable).
6. **Graceful local fallback** — if Teleon is unreachable, Baltor degrades to a local equivalent behind a circuit breaker (the *cloud-defer-only-after-local-equivalent* discipline); Baltor never hard-fails because Teleon is down.
7. **`serves_truth = false` on Teleon output** — capability output is EVIDENCE, not sellable fact; the gateway never emits `served`; Baltor governs truth. Keep this pinned.
8. **Governance > cost, ends stay human** — a governance blocker blocks promotion regardless of a cost/latency win; MEANS (L0–L3) may auto-adapt, ENDS (L5) and `forbidden_autonomous` changes never do.
9. **The seam contract** — frontends reach Teleon only via `/api/teleon/...` (and Observer via `/api/observer/...`), never a hardcoded host.
10. **Vocabulary consistency** — PurposeTask (product) ≡ CapabilityTask (spec, stewarded by OHH); version in metadata, ids minted only by `src.teleon.experiments.ids`.
Source: `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("Cloud hosting topology — separability levers"); `_repos/dev-rules-context/prompts/teleon-build-kit.md` (product invariants 1–6); `_repos/_shared/STANDARDS.md`; `_repos/teleon/backend/src/teleon/agent_gateway/gateway.py`.

## 8. Pointers

- The law (machine source + proof): `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` · `_repos/shared-backend-components/scripts/check_portfolio_dependency_law.py`.
- API surface + hosting topology: `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md`.
- Seam contract: `_repos/shared-backend-components/docs/INTEGRATION-BIBLE.md`; six-component map: `_repos/_shared/ARCHITECTURE-MAP.md`.
- Package boundary: `_repos/teleon/backend/src/teleon/README.md`; agent seam: `_repos/teleon/backend/src/teleon/agent_gateway/gateway.py`.
- The standalone Teleon brief: `_repos/teleon/context/blackbox.md`.
