# Baltor — edges view (how Baltor connects to the other components)

**Purpose of this file.** This is the compatibility contract for managing Baltor separately. It
states Baltor's inbound/outbound interfaces, the same-origin seams, its concrete dependencies on
the other components, and the invariants that must be preserved so a clean cut stays cheap. The
companion `blackbox.md` covers what Baltor internally is/owns/does.

**Grounding.** Every rule here summarizes and links to a machine source or doc (cited inline).
Where a rule is enforced by a proof, that proof is named — the proof, not this prose, is the
authority.

Primary sources synthesized here:

- `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` — the machine source of the dependency law + the Baltor→Teleon migration status (enforced by `_repos/shared-backend-components/scripts/check_portfolio_dependency_law.py`).
- `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` — the Teleon API surface Baltor calls + the hosting/separability corollary.
- `_repos/shared-backend-components/docs/INTEGRATION-BIBLE.md` §1-§2 and `_repos/_shared/ARCHITECTURE-MAP.md` — the seam table.
- `_repos/shared-backend-components/docs/status/baltor-current-state-and-opportunities.md` — the guardrail proofs (no-direct-provider-bypass, tenant isolation, dashboard projection-only, consumption safety).

---

## The dependency law (LAW — enforced, honor it exactly)

```
Baltor ───────────────► Teleon ───────────────► OpenHubForAI (OpenHarnessHub)
(applied product)       (runtime SaaS)          (open ecosystem + spec)
```

- **Baltor MAY depend on Teleon** (calls the Teleon API as tenant `baltor-internal`) and MAY
  depend on **OpenHubForAI**.
- **Teleon MUST NEVER import Baltor** — Teleon is reusable infrastructure, not a Baltor feature.
- **OpenHubForAI MUST import neither** — the open ecosystem/spec stays neutral.

Any forbidden import edge fails the build via `_repos/shared-backend-components/scripts/check_portfolio_dependency_law.py` over
`_repos/shared-backend-components/architecture/portfolio_dependency_law.json`. Branch on the **layer + edge**, never on a brand
display name.
Source: `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` (`law`, `forbidden_edges`); `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("The dependency law").

**Migration gotchas that create an illegal edge (from the law file's `lessons`):** a Baltor→Teleon
move must pre-grep for **lazy, inside-function absolute imports** (e.g.
`from src.baltor.workers...` inside a method) and for **explicit private-name imports**
(`from <mod> import _NAME`, including `_UPPERCASE`) — a top-level import grep misses both and they
reintroduce a `teleon → baltor` edge after a move.
Source: `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` → `migration_status.lessons`.

---

## Outbound: what Baltor consumes from Teleon

Baltor is the internal tenant `baltor-internal`. The extraction of generic runtime concepts
`_repos/baltor/backend/src/baltor → src/teleon` is recorded **COMPLETE** for the fleet/execution substrate, the
Parallel-Path Engine (`experiments`), `purpose_tasks`, and the tenant client — each moved with a
Baltor **re-export shim** so callers and proofs stay green (lossless, never big-bang). Consult
`_repos/shared-backend-components/architecture/portfolio_dependency_law.json` → `migration_status` for the authoritative current
state.
Source: `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` → `migration_status.extracted_so_far` / `to_extract_into_teleon`.

Concrete consumption points:

- **`_repos/baltor/backend/src/baltor/teleon_client/`** (`client.py`) — the versioned tenant client: offline-first local
  execution + graceful fallback from a remote seam + a per-call receipt carrying
  `served_by` / `fallback`. This is Baltor's ONLY sanctioned coupling to Teleon.
  Source: `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` → `migration_status` (STEP 4).
- **Canonical id/hash single source** — Baltor mints data ids/hashes via `src.teleon.experiments.ids`;
  `_repos/baltor/backend/src/baltor/experiments/ids.py` is a re-export **shim** over it (do not add a parallel
  implementation; `import hashlib` in `src/**` is the drift signal — root `CLAUDE.md`
  "Deterministic Global Object Naming").
  Source: `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` → `migration_status.extracted_so_far`; root `CLAUDE.md`.
- **The Teleon API surface** (the boundary Baltor calls as a tenant):
  `POST /purpose-tasks`, `.../run`, `.../evaluate`, `.../run-side-by-side`, `.../promote`,
  `.../rollback`, `.../request-boundary-approval`, `GET .../evidence`, `GET .../customer-assurance`.
  `promote` opens a Promotion + runs the policy engine; it never deploys directly.
  Source: `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("Teleon API surface").

**Failure isolation contract:** if Teleon is unreachable, Baltor **degrades to a local fallback**
behind a circuit breaker and NEVER hard-fails. The per-call receipt records the fallback.
Source: `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("Failure isolation / graceful degrade").

---

## Outbound: what Baltor consumes from OpenHubForAI

OpenHubForAI is the open registry Teleon, Baltor, and AIDevObserver consume; **none of its hubs is a truth authority
(discovery ≠ trust)**. The **method-hub boundary (LOCKED)**: the Baltor method-hubs
(Open{Reconciliation, Hardening, Enrichment, Optimization, Verification}Hub) register **method
SPECS only** as candidates. The motion is: **Baltor SELECTS a method (via Teleon) → RUNS it on
customer data → OWNS the resulting truth.** The spec lives in the store; execution + governed truth
live in Baltor — no duplicated implementation, no moat leak (the moat is the governed data, not the
technique).
Source: `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` (method-hub boundary, lines 54-58).

---

## The seams (same-origin frontend ↔ backend contract)

A Baltor frontend never hardcodes a backend host; it calls a same-origin **seam path** that the
showcase rewrites to the real backend (local service registry by default; `OH_SEAM_*_BASE` in the
cloud). Source of truth: the seam table in `_repos/shared-backend-components/scripts/showcase/server.py`.

| Baltor frontend calls (same origin) | Backend service | Cloud override env |
|---|---|---|
| live-ops (admin/demo) | `baltor_admin_demo_server` | `OH_SEAM_LIVEOPS_BASE` |
| `/api/identity/...` | shared auth / identity (`local_auth_service`) | `OH_SEAM_IDENTITY_BASE` |
| `/registry/...` | Backend registry/catalog projection | `OH_SEAM_REGISTRY_BASE` |
| `/api/teleon/...` | Teleon runtime (`teleon_local_runtime`, 9430) | `OH_SEAM_TELEON_RUNTIME_BASE` |
| `/api/observer/...` | AIDevObserver session review (`observer_runtime`, 9431) | `OH_SEAM_OBSERVER_BASE` |
| `/analytics/...` | event tracking | `OH_SEAM_ANALYTICS_BASE` |

Source: `_repos/_shared/ARCHITECTURE-MAP.md` ("The seams"); `_repos/shared-backend-components/docs/INTEGRATION-BIBLE.md` §1-§2; `_repos/shared-backend-components/scripts/showcase/server.py`.

---

## Inbound: what Baltor exposes to others

- **The governed-context serving surface** — the `ConsumptionService` returning a schema-valid
  `ContextResponse` (every served fact source-handled + receipt-lineaged). The HTTP form
  (`POST /api/context/serve`) is the sequenced target under `OPP-api-serve`.
  Source: `_repos/shared-backend-components/docs/status/baltor-current-state-and-opportunities.md` §19 (OPP-api-serve), §2.
- **Admin/demo + projection APIs** served by `baltor_admin_demo_server` behind the live-ops seam:
  `/api/pipeline/*`, `/api/standards/*`, `/api/memory/*`, `/api/native/*`, `/api/determinism/*`,
  `/api/fleet/*`, `/api/demo/run-full-pipeline-via-fleet` — all **projection-only** (no truth,
  no secrets).
  Source: `_repos/shared-backend-components/docs/status/baltor-current-state-and-opportunities.md` §4.
- **Its usage is observed by AIDevObserver** (session *review*, not code review) over
  `/api/observer/...` — Observer is downstream of usage, not a dependency Baltor imports.
  Source: `_repos/_shared/ARCHITECTURE-MAP.md` §5.

Note the direction: **AI Done Right** (the holding company / parent brand) owns **no runtime code
and no customer data** — Baltor exposes nothing "up" to it (boundary enforced by
`check_company_portfolio_boundaries.py`).
Source: `_repos/_shared/ARCHITECTURE-MAP.md` §1.

---

## Compatibility contracts to preserve (invariants for separate management)

1. **Dependency direction** — never import Baltor from Teleon/OpenHubForAI; only the versioned
   Teleon API + the open spec cross the boundary (`check_portfolio_dependency_law.py`).
2. **No shared database with Teleon** — Teleon owns its runtime/evidence store; Baltor owns
   customer data; integrate via the API + events, never a cross-DB join.
   Source: `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("Separation…").
3. **Canonical id single source** — mint via `src.teleon.experiments.ids`; keep
   `_repos/baltor/backend/src/baltor/experiments/ids.py` a shim; no `import hashlib` in `src/**`.
4. **Agents propose, Baltor disposes** — no agent/LLM ever serves a fact; only reconciliation /
   native_export / distillation / human-gate workers publish truth (worker-taxonomy safety split;
   `RISK-direct-provider-bypass` mitigated by `check_no_direct_provider_bypass.py`).
5. **Dashboards are projection-only** — no truth leakage from any `/api/*` projection
   (`RISK-dashboard-truth-leakage`, `check_architecture_dashboard_projection_only.py`).
6. **Tenant isolation** — `tenant_private` never trains/updates `global_public`
   (`RISK-tenant-isolation`, `check_tenant_isolation_policy.py`).
7. **Consumption never serves an unsafe artifact** (`RISK-consumption-serves-unsafe`,
   `check_consumption_blocks_bad_artifacts.py`).
8. **Lossless** — every distillation/promotion/native-write preserves raw + held-out + rejected +
   lineage; the ORIGINAL is never overwritten; distillation is never replacement
   (`_repos/shared-backend-components/docs/codex/lossless-distillation.md`).
9. **Graceful degrade** — Baltor never hard-fails because Teleon is down.
Source (proof names): `_repos/shared-backend-components/docs/status/baltor-current-state-and-opportunities.md` §21 (risk register) + §4.

---

## Related canonical reading

- `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` — the law + migration status (machine source).
- `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` — roles, Teleon API surface, hosting/separability.
- `_repos/_shared/ARCHITECTURE-MAP.md` — the six-component map + full seam table.
- `_repos/shared-backend-components/docs/INTEGRATION-BIBLE.md` — the frontend↔backend seam contract.
- `_repos/baltor/context/blackbox.md` — the internal view of this component.
