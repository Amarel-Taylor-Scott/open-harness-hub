# AI Done Right — Implementation Handoff

Implementation brief for the platform family (parent + 2 governed products + 21 open
registries). Pair with the per-folder `README.md`s and the project-root `README.md`. The
prototypes are the functional spec; this file is the contract a developer (or Claude Code)
implements against.

## 1. Layout
```
shared/                  design system + site kit (oh-site.*) + brand registry (products.js)
context-is-everything/   parent / portfolio site (AI Done Right) + Demo Control Tower
context-enrichment/      Baltor.ai — paid SaaS · context assurance (app + docs)
teleon/                  Teleon.dev — purpose-driven runtime (reference kit site)
openharnesshub/          OpenHubForAI — bespoke pt-* product site on the kit
open{context,skills,tools,skilltotool,mcp,compression,benchmark,review}hub/
                         9 LIVE registries — config-only via makeHub()
open{templates,endpoint,env,sandbox,agent,receipt,state}hub/ +
open{reconciliation,hardening,enrichment,optimization,verification}hub/  (5 = Baltor engine-stage method hubs)
                         12 PRIVATE-BENCH registries — config-only via makeHub(), status:'private'
```
Separate sites, one foundation. **Branded house**: identical scale/spacing/primitives/fonts;
only the accent color differs. Live hubs use saturated accents; private-bench hubs use a muted
accent + a "Private preview" banner (see §3.5). Brand: **AI Done Right** (`aidoneright.dev`),
tagline *"AI, done right."* — all identity in `products.js`; legacy folder paths kept (see
project `README.md`).

## 2. Shared-layer contract (`shared/`)
- `oh-tokens.css` — colors/space/radii/shadow/type, scoped `{dir-d|dir-s} × {theme-light|theme-dark}`. **Only source of color.**
- `oh-components.css` — canonical primitives + scale vars. **Change once → all sites update.**
  - Surface: `.oh-card` (+`--pad`,`--interactive`); `.pt-panel` (OpenHubForAI) is an alias in the same rule.
  - Controls: `.oh-btn`, `.oh-badge`. Account/interactive: `.oh-tabs/.oh-tab`, `.oh-table`,
    `.oh-segment`, `.oh-field`, `.oh-input`, `.oh-switch`, `.oh-setrow`.
  - Scale (on `.oh`): `--fs-eyebrow/h1/h2/h3/page-title/lead/body/small`, `--pad-card/-panel`,
    `--h-topbar`, `--maxw-site`.
- `products.js` — `window.BRAND` + `window.PRODUCTS`. **One-line brand rename** (`name`/`wordmark`).

### Invariants to preserve when implementing
1. Every card resolves to `.oh-card`. Don't re-declare border/bg/radius per component.
2. `--font-display` = Hanken Grotesk on all three.
3. Size against `--fs-*`/`--pad-*`, never raw px.
4. Parent overrides live at `.oh.dir-s.cie` specificity — don't downgrade to `.cie`.
5. Sites add layout only; they don't fork the shared scale/surface.

## 3. Per-site route maps
**Baltor** (hash): `/` `/why` `/commons` `/docs`(Overview·Guides·Reference·Demos·API)
`/corpora` `/ingest` `/c/:id` `/serve` `/verify` `/governance` `/settings` `/pricing` · NotFound.
**Parent**: single page, anchors `#thesis #architecture #portfolio #proof #fit`.
**Teleon + all 16 hubs**: built on the kit; see §3.5 for the shared hub route map.
**OpenHubForAI**: ~43 routes — see `openharnesshub/PAGES.md` (route → purpose) and `proto-main.jsx` `App()`.

## 3.5 makeHub registry engine (all 21 OpenHubForAI registries)
`shared/oh-hub.jsx` → `makeHub(cfg)` renders an entire registry site from one config object.
Every `<hub>/<hub>-main.jsx` is just that config + a `PORTFOLIO.ENTITIES` entry; bespoke
per-hub surfaces live in the hub folder (e.g. `openskilltotool/os2t-pages.jsx`,
`openreviewhub/orh-pages.jsx`) and attach through gated hooks — the kit stays generic.

**Routes (every hub):** marketing `/` `/browse` `/e/:id` `/cases` `/cases/:id` `/docs`
`/pricing` `/about` `/status` `/changelog` `/terms` `/privacy`; app console `/dashboard`
`/installed` `/publish` `/keys` `/team` `/audit` `/notifications` `/billing` `/usage`
`/settings`; auth `/signin` `/signup` `/forgot`; `/contact`; ⌘K palette. Hash routing.

**Config shape:** `brand{name,tld,glyph,accent}`, `kind`, `themeKey`, `noun/nounPlural/
indefinite`, `heroTitle`, `lede` (+`ledeVariants` → `<hub>_subhead` A/B), `howTitle/howBody`,
`features[[glyph,title,desc]]`, `facets[]`, `installCmd(e)`, `entries[{id,name,by,facet,desc,
installs,score,ver,deps?}]`; optional `standards[[name,desc]]`, `trust(e)` (provenance rows).

**Gated extension hooks (opt-in; a hub that omits them is unchanged):**
- `entryExtra(e, helpers)` → extra cards on the entry-detail page (OpenReviewHub review report,
  OpenSkillToTool converter anatomy).
- `extraRoutes:[{path,navLabel,navIcon,render(helpers)}]` → extra app routes + nav (OpenSkillToTool
  `/architecture`, `/api`).
- `convert:{navLabel,cta,…,render?}` → a `/convert` workbench (hero CTA + nav); `render` replaces
  the default (OpenSkillToTool multi-step wizard).
- `access:'private'` + `openTrigger` → renders the pre-launch banner.

**Private-first / flip-to-public:** a private-bench entity stores a muted `accent` + a saturated
`futureAccent`, a `source` and an `openTrigger`. `products.js` resolves the effective accent from
`status` (keeps `privateAccent`/`launchAccent`); each hub derives `access: E.status==='private'
? 'private' : undefined`. **Opening a hub = one line: `status:'private' → 'live'`** — the muted
accent swaps to the launch color and the banner clears everywhere (parent, hub, Control Tower).
Production must enforce private access server-side (the prototype only hides the banner).

## 4. Theme & flags
- Baltor/Parent: ☾/☀ toggle, `localStorage` `baltor-theme`/`cie-theme`, defaults to
  `prefers-color-scheme`; swaps `theme-light`/`theme-dark` on root.
- OpenHubForAI: route-based theme + scheme override switcher.
- A/B: all live tests run on the **shared experiments engine** (`shared/oh-experiments.js` →
  `OHExp`/`useExperiment`; full guide `EXPERIMENTS.md`). Active experiments: `teleon_hero`,
  `baltor_hero`, `ohh_hero`, and per-hub `<hub>_landing` + `<hub>_subhead` — force via `?exp=key:Variant`, events fan out to `window.dataLayer`
  + `OHExp.onTrack`. Baltor's `useFlag`/`setFlag` are now thin shims over `OHExp`.

## 5. REST contract (Baltor)
The Baltor docs **API** tab is the intended surface: `/v1/corpora`, `/v1/corpora/:id`,
`/v1/corpora/:id/serve`, `/v1/corpora/:id/verify`, `/v1/conflicts/:id/resolve`, `/v1/commons`,
`/v1/commons/:id/subscribe`, `/v1/corpora/:id/artifacts/:type`. Data models are illustrated
by the fixtures in `ce-store.jsx` (`CORPORA`, `CONFLICTS`, `COMMONS`, `PUBLISHERS`,
`REG_CHANGES`, `ARTIFACTS`). Bearer auth.

## 6. Prototype → production gap (must build)
1. Toolchain: Vite/Next with **precompiled JSX** (drop in-browser Babel).
2. Backend + API + datastore + the ingest/verification pipeline (all endpoints mocked now).
3. Auth, persistence, billing (simulated).
4. Replace all fixtures with real data.
5. Split any large JSX further if desired; keep the `Object.assign(window, …)` export pattern
   or migrate to real ESM imports.

## 7. Verification status
Last full sweep (this session): Baltor 14 routes + docs sub-tabs, Parent, OpenHubForAI ~43 routes —
all render, **zero horizontal overflow**, light + dark clean, console clean (only the
expected in-browser Babel dev warning). Scratch screenshot folders removed.

## 8. Migration status & decisions (owner)
**Baltor → kit (done):** auth + contact (`OhAuth`/`OhContact`), Settings (`OhSettings`),
Billing (`OhBilling`), Usage (`OhUsage`), Audit (`OhAuditLog`) and Dashboard (`OhDashboard`,
with Baltor's context-lifecycle grid passed as the new optional `feature` slot) all render via
the shared kit. Baltor's brand color is now single-sourced — the inline accent hex is gone;
its `dir-d` tokens drive light **and** dark (auth pages were previously stuck light-teal in
dark mode — fixed). The retired `.oh.brand-ce` token scope was deleted.

**Deliberately NOT migrated (keep in-house):** Baltor's `AppShell` (sidebar). Its 3-tier
`CEMark` and the "Acme · Compliance / Pro · 4 seats" account footer are brand signatures;
`OhAppShell` would swap them for generic kit chrome. The shell is already 100% token/scale
driven, so it reads as part of the house without conforming structurally. Same rationale
kept the engine grid on the Dashboard. Revisit only if the kit's `OhAppShell` grows a
custom-logo / account-footer slot (the same additive pattern used for `OhDashboard.feature`).

**Major remaining migration:** ~~OpenHubForAI~~ — **done this session.** OpenHubForAI (`openharnesshub/`) now
consumes the shared kit: it loads `oh-site.jsx`; its **app shell** renders via the kit's
`OhAppShell` (extended this session with optional `groups` / `header` / `foot` / `topbar` /
`isActive` slots so OpenHubForAI's grouped collapsible nav, Build menu, credits/account footer and
breadcrumb+⌘K topbar are kept — no dumbing-down); its **account pages** render via `OhSettings`
/ `OhAuditLog` / `OhAuth`; and its **marketing chrome** (landing, use-case pages, preview,
MarketingShell) renders via `OhTopBar` / `OhFooter`. OpenHubForAI keeps its own scheme switcher,
command palette and tweaks (zoom/density/intensity, re-pointed to `.ohs-main`). The kit shell
is adapted to OpenHubForAI's fixed-height root by a 2-line scoped override (`.pt-root > .ohs-app` fills
the viewport; `.ohs-main` scrolls) in `proto.css`.

**Kit extensions made this session (backwards-compatible, additive):** `OhDashboard` gained an
optional `feature` slot + `sub`; `OhAppShell` gained `groups`/`header`/`foot`/`topbar`/`isActive`
+ an `OhNavGroup`; `OhTopBar`'s theme toggle is now opt-in (`onToggle`-gated). A new
**`OhPortfolioMenu`** (cross-site switcher, driven by `window.PORTFOLIO`) lives in every
`OhTopBar` + Baltor's marketing top — it auto-detects the current site and no-ops without the
registry. Teleon and the hubs pass none of the new props and are unaffected.

**Standardized pages + copy (this session):** added shared `OhAbout` (mission page — pulls
`window.BRAND` + renders the family from `PORTFOLIO`) and `OhNotFound` (404); every site now
routes `/about` → `OhAbout` and unknown → `OhNotFound` (Baltor/OpenHubForAI/Teleon/hubs). Teleon's
marketing was repositioned around *unbounded → deterministic*: outcomes **and** guardrails
defined, self-improving/adapts when appropriate, at a fraction of a full agent's token cost
(hero, How-it-works, band + `MARKETING.md`). Its hero example is now the 50-state
maximum-legal-interest-rate task (manual + source-fragile — the case Teleon is built for).

**Token discipline (this session):** the parent's `--cie-baltor`/`--cie-ohh` swatches are now
driven from `PORTFOLIO.ENTITIES` accents at the root (`cie-main.jsx`) — the Baltor swatch had
silently drifted (`#0e8a8f` vs canonical `#0e7c86`); fixed. A duplicate `.oh-switch` block in
`oh-components.css` was de-duped, and OpenHubForAI's one stray `#04130b` now inherits `--accent-ink`.

**Other open items:**
  - **Baltor product-story surfaces (this session):** static `.cd-*` pages in `context-enrichment/`
    — engine overview (`Baltor Engine.html`) + 5 stage deep-dives sharing `engine-stagenav.js`,
    **18 guided demos** (`guided-demo.js`, 11 regulatory domains; held-out value never served),
    two coverage maps, governance report, and `Baltor Where It Fits.html`. Teleon has a parallel
    `#/fits`. See `CLAUDE-CODE.md §3.5`.
  - **Open-standards story (this session):** all 7 hubs have a "Built on the open supply-chain
    stack" landing section; makeHub entry-detail has a per-artifact "Provenance & trust" block;
    Baltor receipts name Sigstore·Rekor / in-toto / CycloneDX AI-BOM. Mapping: `BACKEND-STACK.md`.
  - **Bespoke remaining:** OpenHubForAI's `pt-*` *product* pages (catalog, flow canvas, foundry) — unique
    product UI, not chrome; correctly stay bespoke and compose `.oh-card` via the `.pt-panel`
    alias. Optional future consolidation: extract a shared `OhRegistry` so OpenHubForAI's catalog shares
    render code with the makeHub browse pages.
- Accessibility: a measured contrast pass (this session) nudged every scope's `--fg-faint` to
  clear ≥3.6:1 (was as low as 2.44:1 in light), family-wide via the shared tokens; the shared
  `:focus-visible` ring now restores on text inputs for keyboard users. Still owed: a desktop
  hit-target sweep (44px is a mobile floor; dense desktop controls use 32–36px by design).
  Criterion 9 on the Scorecard reflects this.
- Trademark/domain clearance for **Baltor** + acquisitions (`contextgov.com`, fences).
- Some brand nav labels / CTA strings still inline in JSX (not yet centralized in
  `products.js`) — optional consolidation.
- See `Design Acceptance Scorecard.html` (project root of `openharness/`) for the full
  consistency rubric and current per-site pass/fail.
