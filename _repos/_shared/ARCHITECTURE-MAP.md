# Architecture Map — the six components, their dependency law, and the seams between them

**Purpose.** This is the canonical map of the six components of the portfolio and how they
depend on each other. It is the compatibility contract for the components as they move toward
being managed separately: it states what each component is, which direction one component may
depend on another, and the same-origin seams over which the frontends talk to the backends.

**Grounding.** Every claim here is a summary of, and a link to, an existing repo doc or machine
source. Where a specific rule is enforced by a proof, that proof is named. If this map and a
cited source ever disagree, the cited source wins — this file is a consolidation, not a new
authority.

**Path convention:** short-form citations resolve to the canonical multi-repo layout — `docs/`, `scripts/`,
`architecture/` live under `_repos/shared-backend-components/`; `src/teleon/…` under `_repos/teleon/backend/`;
`src/baltor/…` under `_repos/baltor/backend/`.

Primary sources synthesized here:

- `architecture/portfolio_dependency_law.json` — the machine source of the dependency law (enforced by `scripts/check_portfolio_dependency_law.py`).
- `architecture/substrate_layers.json` — the systems-layer map (enforced by `scripts/check_substrate_layers.py`).
- `docs/strategy/teleon-baltor-openhubforai-portfolio.md` — the canonical brand + dependency architecture (owner-decided 2026-06-06).
- `docs/strategy/computational-substrate-and-foundational-law.md` — the systems-layer reframe + the Foundational Law.
- `docs/INTEGRATION-BIBLE.md` §2 — the seam table (source of truth: the seam table in `scripts/showcase/server.py`).

---

## The six components

### 1. AI Done Right — the parent brand / holding company

The umbrella IP, brands, standards strategy, shared research/security/governance, and cap table.
Its displayed parent brand is **AI Done Right** (`aidoneright.dev`); the code slug
`contextiseverything` remains as a stable identifier. It is the legal/strategic parent, not
prominent to customers at first, and it **owns no runtime code and no customer data** — a
boundary enforced by `check_company_portfolio_boundaries.py`. It sponsors the OpenHubForAI
ecosystem.
Source: `docs/strategy/teleon-baltor-openhubforai-portfolio.md` (portfolio diagram + "Holding company" section).

### 2. Teleon — the runtime SaaS (governs EFFICIENCY)

The purpose-driven, eval-gated, self-adaptive compute runtime SaaS, and its own standalone
product. Teleon **owns**: the PurposeTask / CapabilityTask registry, runtime selection,
implementation candidates, the evidence ledger, promotion gates, policy gates, boundary
approvals, task orientation, the self-adaptation loop, runtime adapters, and the staff/customer
assurance dashboard. Its one-liner: *"Serverless runs code. Kubernetes runs workloads. Teleon
runs purpose."* It is the reference implementation of the open CapabilityTask spec, reusable by
Baltor but not limited to Baltor. Package root: `src/teleon`. Teleon governs what becomes
**EFFICIENT** (the descent brain: make-it-work → make-it-cheap → deterministic substitution).
Source: `docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("Teleon" section); role text in `architecture/portfolio_dependency_law.json` → `layers.teleon`.

### 3. Baltor — the applied context product (governs TRUTH), a Teleon tenant

The customer-facing intelligence system: fully managed, company-/department-/initiative-wide
governed context, **powered by Teleon** as the internal tenant `baltor-internal`. Baltor
**owns**: customer workflows, domain-specific outcomes, source/evidence UX, receipts, customer
workspaces, vertical integrations, and Baltor-specific agents/task-catalogs/business logic. It
**no longer owns directly** the generic adaptive worker runtime, PurposeTask infrastructure,
runtime switching, the promotion/eval control plane, or generic task-dashboard primitives —
those are Teleon's. Package root: `src/baltor`. Baltor governs what becomes **TRUE**; its moat is
the governed data + receipts, not the technique.
Source: `docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("Baltor" section + "Moat split"); role text in `architecture/portfolio_dependency_law.json` → `layers.baltor`.

### 4. OpenHubForAI — the open ecosystem + the open CapabilityTask spec

The open registry that Teleon, Baltor, and AIDevObserver consume: reference context, tools, models, steps, DAG
components, reconciliation/robustness/enrichment rules, modules, skills, harnesses, evals,
templates, and specs. It is a focused **hub family**, not one junk drawer, and **none of its
hubs is a truth authority** (discovery ≠ trust): OpenContextHub (reference context artifacts),
OpenSkillsHub (the open skill graph), OpenToolsHub (the open tool graph), and OpenHubForAI.io
(the proof layer — harnesses, rubrics, eval packs, fixtures, templates, datasets, conformance
packs). The neutral home of the **open CapabilityTask spec (CTS)** — "Teleon implements the open
CapabilityTask Spec," not a proprietary format. Package root: `src/openhubforai`. (This layer is
called `openhubforai` / historically OpenHarnessHub in the dependency law.)
Source: `docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("The OpenHubForAI family" + method-hub boundary); role text in `architecture/portfolio_dependency_law.json` → `layers.openhubforai`.

### 5. AIDevObserver — the AI-usage layer

The layer that watches how intelligence is used and coaches on it: session capture and session
**review** (not code review), AI-usage waste detection, and economics. In the systems-layer map
this is the "AI Usage Waste Engine" (marked **live**): waste detection — oversized PDF to a
frontier model, duplicate context, overprompting, frontier-when-small-suffices,
browser-when-an-API-exists — is live, built on `src/teleon/observer/` (router, review, capture,
session_store), `src/teleon/economics/`, `scripts/check_inefficient_pipeline_archetypes.py`, and
`src/teleon/registry/reinvention_guard.py`. It is the operational form of the execution filter
("remove unnecessary intelligence") and is being grown toward a standalone Observer product.
Frontends reach it over the `/api/observer/...` seam.
Source: `architecture/substrate_layers.json` → `layers[ai_waste_engine]`; `docs/strategy/computational-substrate-and-foundational-law.md` (Layer 5 row); seam in `docs/INTEGRATION-BIBLE.md` §2.

### 6. Backend — the registry / primitives / service-plane substrate

The shared substrate the products sit on: the database-backed registry federation of reusable
components/subcomponents and the seven-primitive model, plus the service-plane of small stdlib
HTTP services behind the seams. The systems-layer map frames this as the "computational
substrate for executable capability" — the registries are the moat substrate (e.g. the
Computational Genome / Primitive Registry, the Infrastructure Registry, the Software Relationship
Graph, the Universal Adapter Factory, the Existing Systems Registry / reinvention guard). Each
frontend talks to this substrate through same-origin seams served by the showcase, never through
a hardcoded host.
Source: `architecture/substrate_layers.json` (layer inventory); `docs/strategy/computational-substrate-and-foundational-law.md` (the reframe + "you already built most of it" table); seam contract in `docs/INTEGRATION-BIBLE.md`.

---

## The architectural law (enforced, not prose)

The dependency direction is a **law**, encoded in `architecture/portfolio_dependency_law.json`
and enforced by `scripts/check_portfolio_dependency_law.py`, which fails the build on any
forbidden import edge. Branch on the layer + edge, never on a brand display name.

```
Baltor ───────────────► Teleon ───────────────► OpenHubForAI (OpenHarnessHub)
(applied product)       (runtime SaaS)          (open ecosystem + spec)
```

- **Baltor depends on Teleon** — it calls the Teleon API as tenant `baltor-internal`. Baltor may also depend on OpenHubForAI.
- **Teleon may consume OpenHubForAI** artifacts (harnesses, templates, skills, the spec).
- **OpenHubForAI depends on neither** — the open ecosystem/spec stays neutral.

**Never the reverse.** The forbidden edges (from `architecture/portfolio_dependency_law.json` →
`forbidden_edges`):

- **Teleon must NEVER import Baltor** — Teleon is reusable infrastructure, not a Baltor feature.
- **OpenHubForAI must never import Baltor** — the open ecosystem must not require the applied product.
- **OpenHubForAI must never import Teleon** — Teleon consumes OpenHubForAI, not the reverse.

Because PurposeTask is **Teleon**, not a Baltor subsystem, generic runtime concepts are being
extracted `src/baltor/` → `src/teleon/` incrementally and losslessly (a module move + a
re-export shim so callers and proofs stay green — never a big-bang). Per
`architecture/portfolio_dependency_law.json` → `migration_status`, the Baltor→Teleon extraction
of the fleet/execution substrate, the Parallel-Path Engine (`experiments`), `purpose_tasks`, and
the tenant client is recorded as **COMPLETE**; consult that file's `migration_status` for the
authoritative, current state rather than trusting this sentence.
Source: `architecture/portfolio_dependency_law.json` (`law`, `forbidden_edges`, `migration_status`); narrative in `docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("The dependency law").

**Separability corollary (why the law matters for separate management).** Teleon and Baltor
co-locate for latency (same region + private network) but stay cleanly separable via: a stable
versioned API contract as the only coupling; **no shared database**; no shared code except via
the open spec / published OpenHubForAI packages; separate identity/billing/IaC; and graceful
local fallback if Teleon is unreachable (Baltor never hard-fails because Teleon is down).
Source: `docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("Cloud hosting topology").

---

## The seams (the standardized frontend ↔ backend contract)

A frontend **never** hardcodes a backend host or port. It calls a same-origin **seam path**; the
serving layer (the showcase) rewrites that seam to the real backend, resolved from the local
service registry by default and overridden by an `OH_SEAM_*_BASE` env in the cloud. The frontend
code is identical locally and in the cloud. The source of truth for the table is the seam table
in `scripts/showcase/server.py`.

| Frontend calls (same origin) | Backend service | Local registry id | Cloud override env |
|---|---|---|---|
| `/api/identity/...` | auth / identity | `local_auth_service` (9410) | `OH_SEAM_IDENTITY_BASE` |
| `/registry/...` | registry / catalog projection | `local_openhubforai_projection_api` (9423) | `OH_SEAM_REGISTRY_BASE` |
| `/analytics/...` | event tracking | `local_event_tracking_service` (9420) | `OH_SEAM_ANALYTICS_BASE` |
| `/api/mailbox/...` | mailbox | `mailbox_local_service` (9428) | `OH_SEAM_MAILBOX_BASE` |
| `/api/teleon/...` | Teleon runtime | `teleon_local_runtime` (9430) | `OH_SEAM_TELEON_RUNTIME_BASE` |
| `/api/observer/...` | AIDevObserver session review | `observer_runtime` (9431) | `OH_SEAM_OBSERVER_BASE` |
| live-ops | Baltor admin / live-ops | `baltor_admin_demo_server` | `OH_SEAM_LIVEOPS_BASE` |

The four load-bearing seams named in the operating instructions map directly onto the components
above: `/api/identity/` (shared auth/identity), `/registry/` (the backend registry/catalog
substrate), `/api/teleon/` (the Teleon runtime), and `/api/observer/` (the AIDevObserver
AI-usage layer). A new frontend↔backend integration is always a service-plane service **plus** a
seam **plus** a `fetch('/api/<x>/...')` — never a hardcoded host.
Source: `docs/INTEGRATION-BIBLE.md` §1–§2.

---

## Related canonical reading

- `docs/strategy/teleon-baltor-openhubforai-portfolio.md` — canonical brand + dependency architecture, hosting topology, Teleon API surface.
- `docs/strategy/computational-substrate-and-foundational-law.md` — the systems-layer reframe + the four-filter Foundational Law.
- `architecture/portfolio_dependency_law.json` — machine source of the law (proof: `scripts/check_portfolio_dependency_law.py`).
- `architecture/substrate_layers.json` — machine source of the layer↔asset↔gap map (proof: `scripts/check_substrate_layers.py`).
- `docs/INTEGRATION-BIBLE.md` — the frontend↔backend seam contract; `docs/DESIGN-BIBLE.md` — the UI counterpart.
