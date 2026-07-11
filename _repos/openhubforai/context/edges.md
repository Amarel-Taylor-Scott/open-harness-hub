# OpenHubForAI — edges view (connections, seams, and compatibility contracts)

**Purpose.** This states how OpenHubForAI connects to the other five components (AI Done Right · Teleon ·
Baltor · AIDevObserver · Backend) and `_shared`: its inbound/outbound interfaces, the same-origin seams, and
the compatibility contracts that must be preserved when OpenHubForAI is managed as a separate codebase. It
explicitly honors the portfolio dependency law. The companion `blackbox.md` covers what OpenHubForAI internally
is and owns.

**Grounding.** Every claim summarizes and links an existing repo doc or machine source. If this file and a
cited source disagree, the source wins.

Primary sources:

- `architecture/portfolio_dependency_law.json` — the machine source of the dependency law (proof: `scripts/check_portfolio_dependency_law.py`).
- `src/openhubforai/__init__.py` + `src/openhubforai/README.md` — the import-freedom law, stated in the package itself.
- `_repos/_shared/ARCHITECTURE-MAP.md` §"The architectural law" + §"The seams" — the portfolio-level law and seam table.
- `docs/strategy/teleon-baltor-openhubforai-portfolio.md` — the dependency law narrative, the hub-family relationship chain, and the method-hub boundary.
- `docs/BIBLE.md` §4 — the RegistryPort ownership boundary and the `maps_to_hub` binding.

---

## 1. The dependency law (OpenHubForAI's position — the hard constraint)

```
Baltor ───────────────► Teleon ───────────────► OpenHubForAI
(applied product)       (runtime SaaS)          (open ecosystem + spec)
```

OpenHubForAI is the **sink** of the dependency arrow: **it depends on neither Teleon nor Baltor.** Teleon
*consumes* OpenHubForAI artifacts (harnesses, templates, skills, the spec); OpenHubForAI never imports them.

**Forbidden edges** (from `architecture/portfolio_dependency_law.json` → `forbidden_edges`; the two that
involve OpenHubForAI):

- **OpenHubForAI must never import Baltor** — the open ecosystem must not require the applied product.
- **OpenHubForAI must never import Teleon** — Teleon consumes OpenHubForAI, not the reverse.

(The third forbidden edge, **Teleon must never import Baltor**, is Teleon's constraint, listed here for the
full picture.)

**Why the neutrality matters:** import-freedom of `src.teleon.*` and `src.baltor.*` is exactly what makes the
standard credibly neutral — *"Teleon implements the open CapabilityTask Spec,"* not "Teleon invented a
proprietary task YAML." Enforced by `scripts/check_portfolio_dependency_law.py`, which fails the build on any
forbidden import edge (branch on the layer + edge, never on a brand display name).
Source: `architecture/portfolio_dependency_law.json` (`law`, `forbidden_edges`, `layers.openhubforai.may_depend_on: []`); `src/openhubforai/__init__.py` (ARCHITECTURAL LAW docstring); `_repos/_shared/ARCHITECTURE-MAP.md` §"The architectural law".

---

## 2. Outbound — what OpenHubForAI exposes to the others (it consumes nothing)

`architecture/portfolio_dependency_law.json` → `layers.openhubforai.may_depend_on` is the empty list: as a
code layer, **OpenHubForAI imports nothing from the other product layers.** All of its edges are things it
*publishes* for others to consume.

- **The open CapabilityTask spec (CTS)** — the standard Teleon implements. `PurposeTask` (product language) and
  `CapabilityTask` (the formal/spec name) are the same object; the spec name is **stewarded by OpenHubForAI**.
  Source: `architecture/portfolio_dependency_law.json` → `vocabulary` + `migration_status.standard_home` ("the open CapabilityTask spec moves under OpenHubForAI (neutral); Teleon = best reference impl; Baltor = flagship vertical"); `docs/spec/OPENHUBFORAI_SPEC.md`.
- **The catalog** — plain-YAML components and reusable capability artifacts under `catalog/` (14 types),
  validated against `schemas/*.schema.json`, with controlled `vocabularies/`. Consumed by Teleon, Baltor, and
  AIDevObserver as the open registry storefront.
  Source: `docs/spec/OPENHUBFORAI_SPEC.md` §1–§2, §7; `docs/strategy/teleon-baltor-openhubforai-portfolio.md` line 14.
- **The 13 standards emitters** — one manifest → 13 published standards formats (`scripts/emit/`). A downstream
  consumer (any registry, vendor, or fork) gets Croissant / MCP server / Agent Skill / HF cards / lm-eval /
  promptfoo / CycloneDX-ML / OpenLineage / C2PA / EU AI Act Annex IV / SPDX 3.0 for free.
  Source: `docs/spec/OPENHUBFORAI_SPEC.md` §6; `scripts/emit/` listing.
- **Eval harnesses · rubrics · primitive/task templates · skills · conformance packs** — the proof layer
  (`OpenHubForAI.io`) that Teleon runs, Baltor consumes in a vertical product, and AIDevObserver searches for
  reuse/candidate-refresh evidence.
  Source: `src/openhubforai/README.md` §"What OpenHubForAI owns" + §"Relationship".

**The relationship chain** (who feeds whom): OpenContextHub supplies context → OpenSkillsHub teaches how →
OpenToolsHub gives execution → **OpenHubForAI proves it works** → **Teleon runs/evolves capabilities** →
**Baltor governs context + decides truth** → AI Done Right coordinates.
Source: `docs/strategy/teleon-baltor-openhubforai-portfolio.md` lines 60–63.

---

## 3. Component-by-component edges

### ↔ Teleon (Teleon consumes OpenHubForAI; never the reverse)

- **Teleon → OpenHubForAI (allowed):** Teleon may import/consume OpenHubForAI artifacts — harnesses,
  templates, skills, the spec. Teleon is the **reference implementation** of the CTS.
  Source: `architecture/portfolio_dependency_law.json` → `layers.teleon.may_depend_on: ["openhubforai"]`.
- **OpenHubForAI → Teleon (FORBIDDEN):** never import `src.teleon.*`.
- **Critical ownership boundary — the registry federation is Teleon's, not OpenHubForAI's.** The
  `RegistryPort`, federated search, and population engines live in `src/teleon/registry/{port,search,populate,
  browse,compose,reinvention_guard,...}.py`. The `RegistryPort` is the single universal query interface across
  the 103 registries and 5 layers. A session managing OpenHubForAI's browse UI **queries registries via that
  Teleon-owned `RegistryPort`; it does NOT rebuild the search.** OpenHubForAI owns the *catalog content, the
  spec, the schemas/vocabularies, and the storefront*; Teleon owns the *federation query engine* that stocks
  and searches it. (This is a runtime consumption edge — the frontend calls the seam, it is not an OHH→Teleon
  Python import.)
  Source: `docs/BIBLE.md` §4 ("Backed by the existing federated search `src/teleon/registry/search.py` + `RegistryPort` `src/teleon/registry/port.py` — do NOT rebuild the search; build the browse UI over it"); `src/teleon/registry/` listing.

### ↔ Baltor (Baltor consumes OpenHubForAI; never the reverse)

- **Baltor → OpenHubForAI (allowed):** Baltor may depend on OpenHubForAI (and on Teleon).
  Source: `architecture/portfolio_dependency_law.json` → `layers.baltor.may_depend_on: ["teleon","openhubforai"]`.
- **OpenHubForAI → Baltor (FORBIDDEN):** never import `src.baltor.*`.
- **The method-hub boundary (LOCKED 2026-06-21) — the key Baltor-facing contract.** The 5 Baltor method-hubs
  (Open{Reconciliation,Hardening,Enrichment,Optimization,Verification}Hub) + OpenRoutingHub are STORE
  components that register **method SPECS only** (candidate; discovery ≠ trust). *Baltor SELECTS a method (via
  Teleon) → RUNS it on customer data → OWNS the resulting truth.* The spec stays in the OpenHubForAI store;
  execution + governed truth live in Baltor, with **no duplicated implementation**. Publishing specs leaks no
  moat because Baltor's moat is the governed DATA + receipts, not the technique.
  Source: `docs/strategy/teleon-baltor-openhubforai-portfolio.md` lines 54–58; `CLAUDE.md` §"Portfolio".

### ↔ AI Done Right (parent brand)

- AI Done Right **sponsors** the OpenHubForAI ecosystem and owns the umbrella IP/brands/standards strategy. It
  owns **no runtime code and no customer data** (enforced by `check_company_portfolio_boundaries.py`). It is
  not a code dependency of OpenHubForAI in either direction.
  Source: `docs/strategy/teleon-baltor-openhubforai-portfolio.md` §"Holding company"; `_repos/_shared/ARCHITECTURE-MAP.md` §1.

### ↔ AIDevObserver (the AI-usage layer)

- No direct code dependency. AIDevObserver is built on `src/teleon/observer/` and reaches frontends over
  `/api/observer/...`. Its relationship to OpenHubForAI is indirect: the reinvention guard
  (`src/teleon/registry/reinvention_guard.py`) grounds its "don't reinvent" coaching on the federated registry
  that stocks the OpenHubForAI catalog — a *runtime* grounding, not an OHH import.
  Source: `_repos/_shared/ARCHITECTURE-MAP.md` §5; `docs/BIBLE.md` §4 (reinvention guard / federated search).

### ↔ Backend (registry / primitives / service-plane substrate)

- The Backend substrate hosts the registry federation and the service-plane services behind the seams. The
  OpenHubForAI catalog is projected to frontends over the `/registry/...` seam by a service-plane service. This
  is a same-origin seam call, not a Python import (and the projection service sits in the substrate/Teleon
  registry code, keeping OpenHubForAI import-free).
  Source: `_repos/_shared/ARCHITECTURE-MAP.md` §6 + §"The seams".

---

## 4. The seam (frontend ↔ backend contract)

A frontend never hardcodes a backend host; it calls a same-origin **seam path** the showcase rewrites to the
real service. The OpenHubForAI-facing seam:

| Frontend calls (same origin) | Backend service | Local registry id (port) | Cloud override env |
|---|---|---|---|
| `/registry/...` | registry / catalog projection (the OpenHubForAI catalog) | `local_openhubforai_projection_api` (9423) | `OH_SEAM_REGISTRY_BASE` |

The `web/openhubforai/` app browses the catalog over `/registry/...`; the same frontend code runs locally and
in the cloud (the seam resolves from the local service registry by default, overridden by `OH_SEAM_REGISTRY_BASE`
in the cloud). A new frontend↔backend integration is always a service-plane service **plus** a seam **plus** a
`fetch('/registry/...')` — never a hardcoded host.
Source: `_repos/_shared/ARCHITECTURE-MAP.md` §"The seams" (source of truth: the seam table in `scripts/showcase/server.py`); `docs/INTEGRATION-BIBLE.md` §1–§2.

---

## 5. Compatibility contracts to preserve when managed separately

These must hold for OpenHubForAI to be developed as its own codebase without breaking the portfolio:

1. **Import-freedom (the neutrality invariant).** `src/openhubforai/**` imports neither `src.teleon.*` nor
   `src.baltor.*`. This is the standard's credibility, not a style rule. Enforced by
   `scripts/check_portfolio_dependency_law.py`.
   Source: `architecture/portfolio_dependency_law.json`; `src/openhubforai/__init__.py`.
2. **The CTS is a stable, versioned, open standard.** The spec shape (14 component types, the shared envelope,
   the DAG composition primitives, the 7 success-criteria kinds) is the contract Teleon implements against.
   Component `version` is semver and lifecycle is a controlled enum; per the repo's data-plane law, a
   component's version lives in metadata, never in a name/id (`@N`/`.vN` are disallowed).
   Source: `docs/spec/OPENHUBFORAI_SPEC.md` §1–§5; `_repos/_shared/STANDARDS.md` §3 (DATA-plane naming: version in metadata).
3. **One manifest → 13 standards publications.** The emitter set (`scripts/emit/`) is a published surface;
   downstream consumers depend on it. Don't silently drop or rename an emitter format.
   Source: `docs/spec/OPENHUBFORAI_SPEC.md` §6.
4. **The federation query engine stays Teleon-owned.** OpenHubForAI provides catalog content + spec + storefront;
   it queries the 103 registries through Teleon's `RegistryPort` (`src/teleon/registry/port.py`) over the
   `/registry/` seam. Do not fork/rebuild the search inside OpenHubForAI.
   Source: `docs/BIBLE.md` §4.
5. **`maps_to_hub` is the only hub↔registry binding** — a registry rolls up to a hub via that field. It is a
   *candidate contract*: nothing yet enforces it stays valid, so a session touching hub/registry structure must
   keep it consistent by hand until a proof exists.
   Source: `docs/BIBLE.md` §4 ("the `maps_to_hub` link is the ONLY explicit hub↔registry binding, and nothing yet enforces it stays valid — a candidate contract").
6. **Discovery ≠ trust: no hub is a truth authority.** OpenHubForAI surfaces (including the method-hubs and any
   discovery/meta registry) publish candidates and pointers; truth is decided downstream in Baltor. Never
   present an OpenHubForAI record as served truth.
   Source: `docs/strategy/teleon-baltor-openhubforai-portfolio.md` §"The OpenHubForAI family" ("none is a truth authority"); `docs/BIBLE.md` §4.
7. **The method-hub execution boundary.** OpenHubForAI holds method SPECS; execution + governed truth stay in
   Baltor (selected via Teleon). Keep the spec in the store and do not duplicate the implementation.
   Source: `docs/strategy/teleon-baltor-openhubforai-portfolio.md` lines 54–58.
8. **Seam discipline.** The `/registry/` seam contract (same-origin path, no hardcoded host, `OH_SEAM_REGISTRY_BASE`
   cloud override) is the only coupling between the OpenHubForAI frontend and its backend.
   Source: `_repos/_shared/ARCHITECTURE-MAP.md` §"The seams"; `docs/INTEGRATION-BIBLE.md`.

---

## 6. Concrete dependency summary

- **Imports FROM other layers:** none (`layers.openhubforai.may_depend_on: []`). OpenHubForAI is import-free of
  Teleon and Baltor by law.
- **Exposes TO other layers:** the open CapabilityTask spec (CTS) · the catalog (14 component types, plain YAML
  + JSON Schema + vocabularies) · the 13 standards emitters · eval harnesses/rubrics/templates/skills/
  conformance packs · the method SPECS registered by the Baltor method-hubs.
- **Consumed by:** Teleon (reference implementation; also owns the `RegistryPort` federation that stocks/queries
  the catalog) and Baltor (applied product; selects method specs, runs via Teleon, owns the truth).
- **Runtime seam:** `/registry/...` → `local_openhubforai_projection_api` (9423) / `OH_SEAM_REGISTRY_BASE`.
Source: `architecture/portfolio_dependency_law.json`; `src/openhubforai/README.md`; `_repos/_shared/ARCHITECTURE-MAP.md` §"The seams".
