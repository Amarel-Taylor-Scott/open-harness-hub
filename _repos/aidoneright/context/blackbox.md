# AI Done Right (parent brand) — blackbox view

**What this file is.** The standalone briefing for a session that manages ONLY the parent
brand. It states what AI Done Right internally is and owns, its surfaces and subsystems, its
current state, and where the detailed docs live. Every claim links to an existing repo source;
where the two disagree, the cited source wins.

**Component identity.** AI Done Right is the parent brand and holding company of the portfolio.
It is component #1 of the six on the canonical map (`_repos/_shared/ARCHITECTURE-MAP.md`).
Display brand: **AI Done Right**, domain `aidoneright.dev`, tagline **"AI, done right."**
Thesis across every property: **discovery is not trust** — take open, discoverable AI building
blocks and turn them into governed, evidence-backed capability.
Sources: `CLAUDE.md` ("Portfolio" section); `_repos/shared-backend-components/dist/sites/aidoneright-design/README.md` (brand
block); `_repos/_shared/design/aidoneright-claude-design/FAMILY-README.md` (Brand section).

---

## What it is and owns

The umbrella IP, brands, standards strategy, shared research / security / governance, and the
cap table. It is the legal and strategic parent (legal entity "AI Done Right, Inc." per
`_repos/shared-backend-components/dist/sites/aidoneright-design/MARKETING.md`), a **house of brands**: governed products (the
moat) sitting on an open registry funnel (lead generation). It sponsors the OpenHubForAI
ecosystem.
Source: `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("Holding company" section);
`_repos/shared-backend-components/dist/sites/aidoneright-design/MARKETING.md` ("Company — AI Done Right").

**Hard ownership boundary (enforced, not prose).** The holding company **owns no runtime code
and no customer data**. `_repos/shared-backend-components/scripts/check_company_portfolio_boundaries.py` proves
`contextiseverything.owned_runtime_surfaces == []` and forbids the parent from holding customer
or runtime data (proof clause B in that script's docstring). A session managing this component
must never add a runtime surface or a customer datastore to the parent.
Source: `_repos/shared-backend-components/scripts/check_company_portfolio_boundaries.py` (docstring clauses B, C, F);
`_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("Holding company").

**Slug and legacy identity.** The displayed brand is "AI Done Right"; the code slug / company
id stays **`contextiseverything`** as a stable identifier, and legacy folder paths
(`context-is-everything/`, repo root `openharness/`, `context-enrichment/` for Baltor) keep
their original names so roughly 20 cross-links in hub footers and the Demo Control Tower do not
break. Paths are invisible to users; renaming any of them requires a full reference sweep.
Source: `_repos/shared-backend-components/dist/sites/aidoneright-design/README.md` ("Legacy paths, current brand");
`_repos/shared-backend-components/dist/sites/aidoneright-design/START-HERE-CLAUDE-CODE.md` §6.

**Founding thesis as legacy context.** The prior "ContextIsEverything" language ("context is
everything"; "it's not the model, it's the context") is preserved as the founding thesis and
legacy path context, not as the parent display brand. Note it is now Baltor's product hook, not
the parent tagline.
Source: `CLAUDE.md` ("Portfolio" section); `_repos/shared-backend-components/dist/sites/aidoneright-design/MARKETING.md`
(Baltor "Primary hook").

---

## Surfaces this component owns

The design snapshot is parent + Baltor + Teleon + AIDevObserver + the OpenHubForAI registries;
the **exact family count is computed, never hand-typed** — run
`python3 _repos/shared-backend-components/scripts/check_ai_done_right_surface_family.py --self-test`. Under the Claude Design
model the parent shows FOUR products at parent level (Baltor, Teleon, AIDevObserver,
OpenHubForAI); the individual Open*Hub registries render inside the OpenHubForAI surface and are
no longer parent-level products.
Source: `_repos/shared-backend-components/scripts/check_ai_done_right_surface_family.py` (header comment); `CLAUDE.md`
("design-family snapshot").

The surfaces owned directly by the parent brand:

- **Parent portfolio site / index** — the "house of brands" landing and portfolio hub.
  Design prototype: `_repos/shared-backend-components/dist/sites/aidoneright-design/context-is-everything/Context is Everything.html`.
  Live web app: `_repos/aidoneright/frontend/` (`cie-main.jsx` + `cie.css`), served by the
  showcase with `OH_PRODUCT=context-is-everything`.
  Source: `_repos/shared-backend-components/dist/sites/aidoneright-design/SYSTEM-INVENTORY.md` (surface 1);
  `_repos/_shared/design/aidoneright-claude-design/FAMILY-README.md` (surface table).
- **Demo Control Tower** — the operator "Start Here" console indexing every site, demo,
  dashboard, and hub (including the private bench) with URLs and status chips. Projection-only
  (it reads the portfolio, serves no truth). File:
  `_repos/aidoneright/frontend/Demo Control Tower.html` /
  `_repos/shared-backend-components/dist/sites/aidoneright-design/context-is-everything/Demo Control Tower.html`.
  Source: `_repos/shared-backend-components/dist/sites/aidoneright-design/README.md` ("Docs in this repo");
  `_repos/shared-backend-components/dist/sites/aidoneright-design/SYSTEM-INVENTORY.md` (surface 2).
- **The shared design system and brand registry** — the parent stewards `shared/` (the whole
  design kit) and `products.js` (the single source of brand + portfolio identity). See the
  edges view for how the other surfaces consume these.
- **Internal projection consoles** (kit-based, no public domain): Shared Inference Gateway
  (`inference-gateway/Shared Inference Gateway.html`) and Shared Template Registry
  (`template-registry/Shared Template Registry.html`). Projection-only.
  Source: `_repos/shared-backend-components/dist/sites/aidoneright-design/SYSTEM-INVENTORY.md` ("Also internal").

**Accent.** One accent per brand. The parent accent is `#5a6b87`
(`_repos/_shared/design/aidoneright-claude-design/FAMILY-README.md` surface table); the marketing guide
calls it "parent blue" (`_repos/shared-backend-components/dist/sites/aidoneright-design/MARKETING.md`, naming rules). Everything
else — type, spacing, chrome, dark-mode mechanism — is identical across the family.

---

## Key subsystems / concepts the parent carries

- **`products.js` — the brand registry (single source of identity).** Holds `BRAND` (AI Done
  Right), `GROUP`, `PORTFOLIO.ENTITIES` (products + hubs, each with
  `name/wordmark/domain/kind/blurb/accent/glyph/url/status`, plus `futureAccent/source/openTrigger`
  for private entries), `LAYERS` (Platform / Open resources / Private bench), and `PORTS`.
  Renaming any brand is a one-line edit here; the parent portfolio and the Demo Control Tower
  pick up the change from `PORTFOLIO`.
  Source: `_repos/shared-backend-components/dist/sites/aidoneright-design/SYSTEM-INVENTORY.md` §2 (`shared/products.js`);
  `_repos/shared-backend-components/dist/sites/aidoneright-design/README.md` ("Shared foundation").
- **The capability lifecycle spine** shown in the parent diagram: Purpose → Contract → Runtime
  selection → Candidate → Evidence → Eval-gated promotion / rollback. Value flows through
  named ports: Baltor → Teleon via `PurposeTaskProviderPort` (Teleon returns evidence /
  candidate / result, never Baltor's own truth), and Teleon → the open hubs.
  Source: `_repos/shared-backend-components/dist/sites/aidoneright-design/MARKETING.md` ("Capability lifecycle spine", "How value
  flows").
- **The one design law.** All surfaces use the SAME shared kit and differ ONLY by their accent
  and their copy. You never style one surface in isolation; you edit a shared kit file once and
  it applies to all. Live surfaces are served by the showcase over `web/<brand>/kit/`; do not
  design against `_repos/shared-backend-components/scripts/surface_server.py` (a demoted fallback, not the live renderer).
  Source: `_repos/_shared/design/aidoneright-claude-design/FAMILY-README.md` ("The one design law");
  `CLAUDE.md` ("Surfaces" section).

---

## Current state

The parent brand is delivered as a **high-fidelity design prototype** (HTML + React 18 via
in-browser Babel, mock data), plus a live web app under `_repos/aidoneright/frontend/` served by
the showcase. The prototype is the implementation spec, not production code. A production build
must add: a real toolchain (Vite/Next with precompiled JSX), backends and datastores, real auth
/ persistence / billing, and real data in place of every fixture. All 24 surfaces render with
zero horizontal overflow, clean in light and dark, console clean apart from the expected
in-browser Babel dev warning; the branded-house consistency gate is
`Design Acceptance Scorecard.html` (family reported at 94%).
Source: `_repos/shared-backend-components/dist/sites/aidoneright-design/START-HERE-CLAUDE-CODE.md` §5, §7;
`_repos/shared-backend-components/dist/sites/aidoneright-design/README.md` ("Prototype vs. production").

Formal trademark / domain clearance for the parent brand and the proposed `.io` hub domains
remains owner-gated before heavy public use.
Source: `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("Holding company");
`_repos/shared-backend-components/dist/sites/aidoneright-design/MARKETING.md` ("The open layer", closing note);
`_repos/shared-backend-components/scripts/check_company_portfolio_boundaries.py` (docstring clause G).

---

## Pointers to the detailed docs

The full parent-brand design reference bundle (now under `_repos/shared-backend-components/dist/sites/aidoneright-design/`):

- `_repos/shared-backend-components/dist/sites/aidoneright-design/START-HERE-CLAUDE-CODE.md` — the paste-ready kickoff, reading
  order, and the prototype→production gap. Read first.
- `_repos/shared-backend-components/dist/sites/aidoneright-design/README.md` — family overview, the `makeHub` engine, and
  flip-to-public.
- `_repos/shared-backend-components/dist/sites/aidoneright-design/CLAUDE-CODE.md` — developer orientation and what to port first.
- `_repos/shared-backend-components/dist/sites/aidoneright-design/HANDOFF.md` — the implementation contract (shared-layer
  contract, route maps, rename points).
- `_repos/shared-backend-components/dist/sites/aidoneright-design/DESIGN-CONTRACT.md` — enforcement rules that override anything
  more permissive.
- `_repos/shared-backend-components/dist/sites/aidoneright-design/SYSTEM-INVENTORY.md` — the reuse-first manifest of every
  surface, module, export, experiment, and theme key.
- `_repos/shared-backend-components/dist/sites/aidoneright-design/MARKETING.md` and `POSITIONING-AUDIT.md` — canonical positioning
  and copy; category-language alignment.
- `_repos/shared-backend-components/dist/sites/aidoneright-design/BACKEND-STACK.md` and `EXPERIMENTS.md` — per-registry backend
  building blocks; the shared A/B engine.
- `_repos/_shared/design/aidoneright-claude-design/FAMILY-README.md`, `_repos/shared-backend-components/docs/DESIGN-BIBLE.md`,
  `_repos/shared-backend-components/docs/INTEGRATION-BIBLE.md` — the current Claude Design family handoff (tokens, components, the
  frontend↔backend seam contract).
- `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` — canonical brand + dependency
  architecture (owner-decided 2026-06-06).
- `_repos/_shared/ARCHITECTURE-MAP.md` — the six-component map; parent = component #1.

See `edges.md` in this folder for how the parent connects to the other five components and the
compatibility contracts to preserve.
