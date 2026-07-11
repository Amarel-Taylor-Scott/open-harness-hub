# AI Done Right (parent brand) — edges view

**What this file is.** How the parent brand connects to the other five components and to
`_shared`: its inbound and outbound interfaces, the seams, and the compatibility contracts that
must hold when the parent is managed as a separate component. Every claim links to an existing
repo source; where the two disagree, the cited source wins. The canonical cross-component map is
`_repos/_shared/ARCHITECTURE-MAP.md` (parent = component #1).

## Where the parent sits in the dependency law

The runtime dependency law is **Baltor → Teleon → OpenHubForAI (OpenHarnessHub), never the
reverse**, enforced by `_repos/shared-backend-components/scripts/check_portfolio_dependency_law.py` over
`_repos/shared-backend-components/architecture/portfolio_dependency_law.json`. The parent brand is the HoldCo / umbrella above
that chain, not a link in the import graph: it sponsors OpenHubForAI and owns the brands, but it
holds no runtime code. The parent's own boundary proof
(`_repos/shared-backend-components/scripts/check_company_portfolio_boundaries.py`) is kept **consistent with** the import law —
`contextiseverything.owned_runtime_surfaces == []` and the ownership map must not contradict the
dependency law (clauses B, C).
Source: `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` (`law`, `forbidden_edges`);
`_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("The dependency law");
`_repos/shared-backend-components/scripts/check_company_portfolio_boundaries.py` (docstring).

The forbidden edges the parent must never help create, since it stewards the brand registry and
the parent diagram that describe these relationships:

- Teleon must NEVER import Baltor (Teleon is reusable infrastructure, not a Baltor feature).
- OpenHubForAI must never import Baltor or Teleon (the open ecosystem stays neutral).
- Baltor must never own generic Teleon concepts (PurposeTask is Teleon, not a Baltor subsystem).

Source: `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` (`forbidden_edges`);
`_repos/_shared/ARCHITECTURE-MAP.md` ("The architectural law").

---

## Inbound — what other components consume from the parent

The parent's outputs are design and identity artifacts, not runtime calls:

- **The shared design kit (`shared/` → `web/<brand>/kit/`).** Every surface (Baltor, Teleon,
  AIDevObserver, OpenHubForAI, and the 21 hubs) renders from the SAME shared kit and differs
  only by accent and copy. Editing a shared kit file once (a token in `oh-tokens.css`, a
  component in `oh-site.jsx`) changes all surfaces.
  Source: `_repos/_shared/design/aidoneright-claude-design/FAMILY-README.md` ("The one design law");
  `_repos/shared-backend-components/dist/sites/aidoneright-design/README.md` ("Shared foundation").
- **The brand registry (`shared/products.js`).** The single source of brand + portfolio
  identity: `BRAND`, `GROUP`, `PORTFOLIO.ENTITIES` / `LAYERS` / `PORTS`, per-brand accents, and
  the status-aware accent resolver. Other surfaces and the portfolio index read from it rather
  than forking brand copy.
  Source: `_repos/shared-backend-components/dist/sites/aidoneright-design/SYSTEM-INVENTORY.md` §2 (`shared/products.js`);
  `_repos/shared-backend-components/dist/sites/aidoneright-design/README.md` ("`products.js`").
- **The portfolio taxonomy read by the parent's own surfaces.** The parent portfolio page and
  the Demo Control Tower enumerate every surface from `PORTFOLIO` (projection-only; they serve
  no truth). Adding an entity to `ENTITIES` + `LAYERS` makes the parent and the Control Tower
  pick it up automatically.
  Source: `_repos/shared-backend-components/dist/sites/aidoneright-design/README.md` ("Add a new site");
  `_repos/shared-backend-components/dist/sites/aidoneright-design/SYSTEM-INVENTORY.md` (surfaces 1–2).

---

## Outbound — what the parent consumes from others

- **At runtime: nothing.** The parent owns no runtime code and no customer data, so it imports
  no product runtime. It links to the products (Baltor, Teleon, AIDevObserver, OpenHubForAI)
  and reflects their status, but it does not call their business logic.
  Source: `_repos/shared-backend-components/scripts/check_company_portfolio_boundaries.py` (clause B);
  `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("Holding company").
- **The parent diagram references the value-flow ports** it does not itself own: Baltor → Teleon
  via `PurposeTaskProviderPort`, and Teleon → the open hubs. These are illustrative of the
  portfolio it coordinates, not parent-owned code.
  Source: `_repos/shared-backend-components/dist/sites/aidoneright-design/MARKETING.md` ("How value flows (ports)").

---

## Seams (frontend ↔ backend)

The live parent app (`_repos/aidoneright/frontend/`) is served by the showcase
(`OH_PRODUCT=context-is-everything python3 -m scripts.showcase --port N`) over the shared kit.
A frontend never hardcodes a backend host; it calls a same-origin seam path that the showcase
rewrites to the real service. The seam table (source of truth: the seam table in
`_repos/shared-backend-components/scripts/showcase/server.py`) is reproduced in `_repos/_shared/ARCHITECTURE-MAP.md`. The
parent app is chiefly a marketing / portfolio index; the kit's account and auth flows it inherits
reach identity over `/api/identity/...`, and the portfolio / Control Tower reflect status from
the registry. The four load-bearing seams are `/api/identity/`, `/registry/`, `/api/teleon/`,
and `/api/observer/`.
Source: `_repos/_shared/design/aidoneright-claude-design/FAMILY-README.md` ("How the live system actually
works"); `_repos/shared-backend-components/docs/INTEGRATION-BIBLE.md` §1–§2; `_repos/_shared/ARCHITECTURE-MAP.md` ("The seams").

---

## Compatibility contracts to preserve (when managed separately)

1. **Parent owns no runtime code and no customer data.** Keep
   `contextiseverything.owned_runtime_surfaces == []`; never add a runtime surface or customer
   datastore under the parent. Enforced by `_repos/shared-backend-components/scripts/check_company_portfolio_boundaries.py`
   (clause B) and consistent with the dependency law (clause C).
2. **The dependency law is untouched by parent changes.** Baltor → Teleon → OpenHubForAI, never
   reverse; Teleon never imports Baltor; OpenHubForAI imports neither. Enforced by
   `_repos/shared-backend-components/scripts/check_portfolio_dependency_law.py` over `_repos/shared-backend-components/architecture/portfolio_dependency_law.json`.
3. **`products.js` is the single source of brand identity.** Renames are one-line edits there;
   other surfaces read from it. Do not fork brand names, taglines, or accents into per-surface
   copy. Source: `_repos/shared-backend-components/dist/sites/aidoneright-design/MARKETING.md` ("Naming & relationship rules");
   `_repos/shared-backend-components/dist/sites/aidoneright-design/SYSTEM-INVENTORY.md` §2.
4. **Legacy slug and paths are stable.** The slug / company id stays `contextiseverything`;
   legacy folders (`context-is-everything/`, `context-enrichment/`, root `openharness/`) are not
   renamed without a full cross-link sweep (~20 links in hub footers and the Demo Control Tower).
   Source: `_repos/shared-backend-components/dist/sites/aidoneright-design/README.md` ("Legacy paths, current brand");
   `_repos/shared-backend-components/dist/sites/aidoneright-design/START-HERE-CLAUDE-CODE.md` §6.
5. **The one design law holds.** The shared kit is the only style source; accent and copy are
   the only per-surface variables. Do not design against `_repos/shared-backend-components/scripts/surface_server.py` (a demoted
   fallback). Source: `_repos/_shared/design/aidoneright-claude-design/FAMILY-README.md` ("Do not
   regress"); `CLAUDE.md` ("Surfaces" section).
6. **The family count is computed, never hand-typed.** Verify with
   `python3 _repos/shared-backend-components/scripts/check_ai_done_right_surface_family.py --self-test` before trusting or editing
   any surface-family count. Source: `CLAUDE.md` ("design-family snapshot").
7. **Discovery is not trust.** The parent must not present private-bench hubs as public
   production surfaces, or present OpenHubForAI discovery as governed truth (only Baltor's
   governed source serves truth). Source:
   `_repos/_shared/design/aidoneright-claude-design/FAMILY-README.md` ("Do not regress");
   `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("The OpenHubForAI family").

---

## The other five components (one line each)

- **Teleon** — the runtime SaaS (governs EFFICIENCY); parent links to it, owns none of its code.
  See `_repos/teleon/context/`.
- **Baltor** — the applied context product (governs TRUTH), a Teleon tenant `baltor-internal`.
  See `_repos/baltor/context/`.
- **OpenHubForAI** — the open ecosystem + the open CapabilityTask spec; sponsored by the parent.
  See `_repos/openhubforai/context/`.
- **AIDevObserver** — the AI-usage layer; reached over `/api/observer/`. See
  `_repos/aidevobserver/context/`.
- **Backend** — the registry / primitives / service-plane substrate behind the seams. See
  `_repos/shared-backend-components/context/`.

Full map and seam table: `_repos/_shared/ARCHITECTURE-MAP.md`.
