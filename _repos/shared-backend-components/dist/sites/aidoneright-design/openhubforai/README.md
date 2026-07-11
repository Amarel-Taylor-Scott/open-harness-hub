# openhubforai/ — OpenHubForAI

The open, free **funnel** product: build governed harnesses (composed pipelines of
primitives) and consume Baltor's verified context. Hash-routed React SPA, ~43 routes.

Entry: **`OpenHubForAI.html`** → open in a browser.

## Read these first
- **`PAGES.md`** — the canonical route → purpose catalog (every page).
- **`HANDOFF.md`** — full implementation handoff & file inventory (this product). Note: it
  predates the family-wide rebrand; for the *family* contract (shared layer, branded-house
  rules, Baltor naming) see the project-root `../README.md` and `../HANDOFF.md`.

## Shape
- `proto-main.jsx` — router + `App()` + the kit-based `AppShell`/`MarketingShell`; the route map
  lives here (source of truth).
- `proto-store.jsx` — mock data + flags/tweaks.
- `proto.css` + `proto-*.css` — layout. Surfaces use `.pt-panel`, which is a **compatibility
  alias of the shared `.oh-card`** (defined in `../shared/oh-components.css`).
- `proto-*.jsx` — page groups (build, catalog, admin/billing, value, byo, ops, sdg, wide, …).
- `oh-artifacts.jsx` — review/artifact helpers. `explorations/` — design-decision canvas.

## House style
- Scope `oh dir-s` + route-based theme (marketing `theme-light`, app `theme-dark`) + a
  scheme override switcher. Accent = ember.
- Display font now **Hanken Grotesk** (shared `--font-display`); scale from shared `--fs-*`.
- A/B flags via `localStorage('ohp-flags')` / `?flags=…`; tweaks via `localStorage('ohp-tweaks')`.

## Branded-house integration
OpenHubForAI shares the design system in `../shared/` **and now consumes the shared SITE KIT**
(`../shared/oh-site.*`, loaded in the HTML):
- **Chrome** is the kit. `proto-main.jsx` `AppShell` renders the kit's `OhAppShell` (OpenHubForAI's
  grouped collapsible nav, Build menu, credits/account footer and breadcrumb+⌘K topbar are
  passed as the kit's `groups`/`header`/`foot`/`topbar` slots). Marketing top bars + footers
  (landing, `/for/*`, `/preview`, `MarketingShell`) render the kit's `OhTopBar`/`OhFooter`.
  The landing also carries the family-wide **"Built on the open supply-chain stack"** section
  (Sigstore · SLSA+in-toto · lm-evaluation-harness · CycloneDX AI-BOM · OpenSSF Scorecard ·
  SemVer), built with the shared `.oh-card` primitive to match the six makeHub hubs.
- **Account pages** are the kit: `/settings` → `OhSettings`, `/audit-log` → `OhAuditLog`,
  `/signin`+`/signup` → `OhAuth`.
- **Product pages stay bespoke** `pt-*` (catalog, flow canvas, foundry, registry, …) — unique
  product UI, composing the shared `.oh-card` via the `.pt-panel` alias.
- OpenHubForAI keeps its own **scheme switcher, command palette and tweaks** (text-size / density /
  intensity); the tweak zoom/filter selectors include `.ohs-main` (the kit shell's scroller).
- Structural tie-ins to keep intact: `.pt-panel` must stay in the `.oh-card` alias group in
  `oh-components.css`; the 2-line `.pt-root > .ohs-app` / `.ohs-main` override in `proto.css`
  adapts the kit's page-scroll shell to OpenHubForAI's fixed-height root.
