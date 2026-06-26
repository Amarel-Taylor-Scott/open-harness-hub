# Claude Code Handoff — AI Done Right

> Brand: **AI Done Right** (`aidoneright.dev`, *"AI, done right."*). The platform (Baltor,
> Teleon) is the company; the `OpenHubForAI` sites are the open, top-of-funnel lead-gen. Folder/
> file paths keep their **legacy names** (`context-is-everything/`, repo root `openharness/`)
> so ~20 cross-links don't break — only the displayed brand changed. See `CLAUDE.md`.
>
> ⚠ **`DESIGN-CONTRACT.md` governs this implementation and overrides anything more
> permissive in this file.** Port the CSS verbatim, transplant the JSX, keep all copy
> verbatim, no library substitutions, and run the per-surface parity gate. A previous
> implementation drifted; the contract exists so this one can't.

Read this first, then `README.md` (family overview) and `HANDOFF.md` (implementation
contract). This file is the orientation + integration guide for building the family in a real
codebase.

---

## 1. What this is (and isn't)
This repo is a **high-fidelity, interactive design spec** for a portfolio of **~24 surfaces**
(parent + 2 governed products + 21 open registries) under one platform company. It is built in
**HTML + React-via-in-browser-Babel with mock
data** — that is a *prototyping* choice, **not** the production stack. The screens, flows, IA,
copy, interactions and the full design system are the spec; **transplant them into the target
codebase per `DESIGN-CONTRACT.md`** — the CSS and config files ship verbatim; the JSX keeps its
element tree and class names (or, if no stack exists, pick a modern one — see §6).

**Fidelity: high.** Final colors, type, spacing, dark mode, copy and interactions are intended
as-is. Recreate pixel-faithfully using the target codebase's libraries; do not ship the
prototype HTML directly.

The surfaces (entry HTML in each folder) — **full table in `README.md`**:
| Group | Sites |
|---|---|
| Parent | AI Done Right (`context-is-everything/`, blue) |
| Products | Baltor.ai (`context-enrichment/`, teal) · Teleon.dev (`teleon/`, violet) |
| Live hubs (makeHub) | OpenContextHub · OpenSkillsHub · OpenToolsHub · OpenSkillToTool · OpenMCPHub · OpenCompressionHub · OpenBenchmarkHub · OpenReviewHub · OpenHarnessHub |
| Private bench (makeHub, `status:'private'`) | OpenTemplatesHub · OpenEndpointHub · OpenEnvHub · OpenSandboxHub · OpenAgentHub · OpenReceiptHub · OpenStateHub · **+ 5 Baltor-stage method hubs:** OpenReconciliationHub · OpenHardeningHub · OpenEnrichmentHub · OpenOptimizationHub · OpenVerificationHub |

> Folder note: `context-enrichment/` IS Baltor (historical key). See `CLAUDE.md` at the repo root.
> **All 21 OpenHubForAI registries render from `makeHub` (config-only)** — 9 live + 12 private bench. Bespoke
> per-hub surfaces (OpenSkillToTool's `os2t-pages.jsx`, OpenReviewHub's `orh-pages.jsx`) are
> folder-local and composed via makeHub's gated hooks (`entryExtra` / `extraRoutes` /
> `convert.render`), so the kit stays generic. **Private-bench hubs use a muted accent + a
> "Private preview" banner** (`access:'private'`) and store a saturated `futureAccent`; opening
> one is a one-line `status:'private' → 'live'` flip (accent + banner resolve automatically).
> OpenHarnessHub is the one bespoke `pt-*` site — chrome + account pages on the shared kit,
> catalog composes `.oh-card` via the `.pt-panel` alias; only its builder pages are bespoke.

---

## 2. The core idea: a *branded house* on one kit
Identical type scale, spacing, primitives, fonts, chrome and dark-mode mechanism across every
site — **only the accent color differs.** This is the single most important constraint
to preserve when you implement. Everything flows from `shared/`:

- **`shared/oh-tokens.css`** — all color/space/radii/shadow/type tokens, scoped
  `{dir-a|dir-s|dir-d|cie} × {theme-light|theme-dark}`. **Only source of color.** Never hardcode
  a hex in a site stylesheet.
- **`shared/oh-components.css`** — canonical primitives + the scale vars (`--fs-*`, `--pad-*`,
  `--h-topbar`, `--maxw-site`). `.oh-card`, `.oh-btn`, `.oh-badge`, `.oh-tabs`, `.oh-table`,
  `.oh-segment`, `.oh-field`, `.oh-input`, `.oh-switch`, `.oh-setrow`. Change a primitive here →
  every site updates.
- **`shared/oh-site.css` + `oh-site.jsx`** — the **SITE KIT** (the thing to port to real
  components first; see §3).
- **`shared/oh-hub.css` + `oh-hub.jsx`** — `makeHub(cfg)`: an entire open-registry site from one
  config object. All 21 OpenHubForAI registries are config-only (9 live + 12 private bench).
- **`shared/products.js`** — single source of truth for brand identity + the `PORTFOLIO`
  registry. **Brand renames are one-line edits here.** Messaging guide: `MARKETING.md`.
- **`shared/oh-experiments.js`** — framework-agnostic A/B + event-tracking engine
  (`window.OHExp`), with `useExperiment` / `OhExperimentsPanel` in the kit. Sticky weighted
  assignment, `?exp=key:variant` overrides, events pushed to `window.dataLayer` + `onTrack`
  sinks (GA4 / Segment / PostHog wire in with no app changes). Full guide: `EXPERIMENTS.md`.

A new brand = a config object + **one** inline `--accent` CSS var. It inherits everything else.

---

## 3. The SITE KIT — port these components first
`shared/oh-site.jsx` is the heart. Build these as real, reusable components in your framework;
every site composes them. (Props shown are the prototype's shape — adapt to your conventions.)

**Chrome**
- `OhTopBar({ brand, nav, cta, signInHref, theme?, onToggle? })` — marketing top bar. Theme
  toggle renders only if `onToggle` is passed. Includes the cross-site **`OhPortfolioMenu`**.
- `OhPortfolioMenu()` — cross-site app switcher driven by `window.PORTFOLIO` (products.js).
  Groups entities by `LAYERS`, auto-detects the current site from the URL, no-ops if PORTFOLIO
  is absent. Appears in every `OhTopBar` + Baltor's marketing top.
- `OhAppShell({ brand, nav | groups, header?, foot?, topbar?, isActive?, route, cta, theme, onToggle, children })`
  — signed-in app shell (sidebar + main). Supports a **flat `nav`** OR **grouped collapsible
  `groups`** (`[{label, items:[[href,glyph,label]], defaultOpen}]`), plus optional `header`
  (above nav), `foot` (replaces default footer), `topbar` (sticky bar over the page), and
  `isActive(href)` override. OHH uses every slot; Teleon/hubs use plain `nav`.
- `OhFooter({ brand, tagline, cols })`.

**Marketing skeletons:** `OhHero`, `OhSection`, `OhFeatures`, `OhBand`, `OhPageHead`, `OhRollup`.

**Primitive pages (every brand reuses these — build once):** `OhAuth` (signin/signup/forgot),
`OhContact`, `OhPricing`, `OhBilling`, `OhUsage`, `OhSettings` (`sections:[{title, rows:[{t,d,ctrl}]}]`),
`OhDashboard` (now with optional `feature` slot + `sub`), `OhApiKeys`, `OhTeam`, `OhAuditLog`,
`OhDocs`, `OhStatus`, `OhChangelog`, `OhLegal` (`kind:'terms'|'privacy'`), **`OhAbout`** (mission
page — reads `window.BRAND` + renders the family from `PORTFOLIO`), **`OhNotFound`** (standardized
404; `home` + optional suggestion `links`), **`OhCaseStudies`** (index grid) + **`OhCaseStudy`**
(detail; `cases` + `id`), **`OhCommandK`** (⌘K command palette — `commands:[{label,href,icon,group}]`
or `OhCommandK.fromNav(nav, groups)`; opens on ⌘K / a `oh-cmdk` window event; tracks `cmdk_select`).
Plus the shared hooks `useHashRoute`, `navigate`,
`useSiteTheme`. **Convention:** every site routes `/about` → `OhAbout`, `/cases` → `OhCaseStudies`,
`/cases/:id` → `OhCaseStudy` (studies live in `shared/cases.js` as `window.CASES[brandId]`), and
unknown → `OhNotFound`. The parent surfaces one flagship case per product brand in a "Proof"
section deep-linking into each site's `/cases/:id`.

**Who's built on what (current state — all verified):**
- **Teleon + the 3 hubs** — 100% on the kit (hubs via `makeHub`). Pure config + a few unique pages.
- **Baltor** — its account layer (auth, contact, settings, billing, usage, audit) + dashboard
  render via the kit; it keeps an in-house sidebar `AppShell` on purpose (its 3-tier brand mark
  + account footer are brand signatures), fully token/scale-driven.
- **OHH** — chrome + account pages on the kit (`OhAppShell` with its grouped nav/Build/credits/
  topbar passed as slots; `OhSettings`/`OhAuditLog`/`OhAuth`; `OhTopBar`/`OhFooter`). Its unique
  **product** pages (catalog, flow canvas, foundry, registry…) stay bespoke `pt-*`, composing
  `.oh-card`. It keeps a command palette, scheme switcher, and tweak controls.

---

## 3.5 Baltor product-story surfaces (static HTML, `context-enrichment/`)
Beyond the React app, Baltor ships a set of **static narrative surfaces** (`.cd-*` layer in
`guided-demo.css`, dir-d teal) that sell the governed-context engine. Recreate these as marketing
/ product-education pages:
- **`Baltor Engine.html`** — the engine overview hub: 4 pillars (Verified · Current · Efficient ·
  Provable) + the 5-stage pipeline (Reconcile · Harden · Enhance · Optimize · Verify), each
  routing to its deep-dive.
- **Five stage deep-dives** — `Baltor Reconciliation Deep-Dive.html`, `Baltor Anti-Fragility
  Deep-Dive.html` (titled **Hardening** on-surface; "anti-fragility" is internal-only),
  `Baltor Enhancement Deep-Dive.html`, `Baltor Optimization Showcase.html`, `Baltor Receipts
  Explorer.html`. All share `engine-stagenav.js` (one sticky cross-stage nav; mount with
  `mountStageNav('<key>')`).
- **`Baltor Guided Demos.html`** — index of **18 worked data examples** across 11 regulatory
  domains; each example is one `SCENARIOS` object in `guided-demo.js` (a 7-stage governed run
  that serves a verified answer and **holds the contradiction out, never served**). Adding a
  domain = one scenario object + a thin shell HTML + an index entry. Domains: CFPB/Reg E, OFAC
  sanctions, EUDR, refund policy, HS tariff, dangerous goods, transit SLA, marine fuel, water
  (EPA), freight HOS, oil reserves, FDA, ICD, OSHA, minimum wage, export controls (EAR), FAA
  airworthiness, FASB effective date.
- **Coverage maps** — `Baltor Federal Register Coverage.html` (50 CFR titles, 11 with worked
  demos + change feed) and `Baltor International Coverage.html` (EU/IMO/IATA/WCO/WHO/Codex/ILO/ISO
  + state/local + contractual). **`Baltor Context Governance Report.html`** (the audit-output
  artifact) and **`Baltor Where It Fits.html`** (honest OSS-landscape positioning).
- **Tracking:** these static pages load `shared/oh-experiments.js` + `track.js` (declarative
  `data-track="event" data-tp-*` attributes) → events flow to `window.dataLayer` like the rest.

**Teleon** has a parallel **`#/fits`** route (honest OSS-landscape page) in `teleon-main.jsx`.

## 3.6 Open-standards / supply-chain story (all 7 hubs)
Every hub landing has a **"Built on the open supply-chain stack"** section, and every makeHub
entry-detail has a per-artifact **"Provenance & trust"** block. The prototypes' vocabulary maps
to real standards — implement against these, don't reinvent: **receipt** = Sigstore/Rekor,
**AIBOM** = OWASP CycloneDX AI-BOM, **provenance** = SLSA + in-toto, hub **risk score** /
`RepoIntelClassifier` = OpenSSF Scorecard, **related-artifacts graph** = GUAC. Eval hubs use
lm-evaluation-harness / Inspect; compression uses LLMLingua; MCP uses the official MCP registry +
MCPTox. Full per-site backend map: **`BACKEND-STACK.md`**.

---

## 4. Tech shape of the prototype (so you can read it)
- React 18 via in-browser Babel (`<script type="text/babel">`), pinned CDN + integrity hashes.
- **Hash routing** (`#/route`), no router lib — see each site's `*-main.jsx` `App()` for the map.
- Each Babel file gets its own scope; cross-file sharing is `Object.assign(window, {…})`.
- Mock data only; no backend, no network calls.
- Dark mode: a `☾/☀` toggle persisted to `localStorage`, defaulting to `prefers-color-scheme`
  (swaps `theme-light`/`theme-dark` on the root). OHH adds a route-based theme + scheme switcher.

---

## 5. Route maps & data models
- **Baltor:** `/` `/why` `/engine` `/commons` (Verified corpora) `/docs` `/corpora` `/ingest`
  `/c/:id` `/serve` `/verify` `/governance` `/dashboard` `/sources` `/pipeline` `/audit`
  `/settings` `/billing` `/usage` `/pricing` `/signin /signup /forgot /contact`. The Baltor docs
  **API** tab is the intended REST contract; fixtures live in `context-enrichment/ce-store.jsx`.
- **OHH:** ~43 routes — catalog in `openharnesshub/PAGES.md`; map in `proto-main.jsx` `App()`.
- **Parent:** single page with anchors. **Teleon / hubs:** see each `*-main.jsx`.

---

## 6. Prototype → production (what a real build must add)
1. **Toolchain:** Vite or Next with **precompiled JSX** — drop in-browser Babel. Port `shared/`
   to real modules (CSS tokens can stay as CSS variables / a Tailwind theme; the kit components
   become your component library).
2. **Backend + API + datastore** + the ingest / verification / engine pipelines (all mocked now).
   Baltor's `/v1/*` surface in the docs API tab is the intended contract.
3. **Auth, persistence, billing** (currently simulated).
4. **Replace fixtures with real data** (corpora, conflicts, runs, usage are illustrative).
5. Keep the **branded-house invariants** (§2) and the **Design Acceptance Scorecard** green
   (`Design Acceptance Scorecard.html` — open in a browser; it lists the exact check per
   criterion). Re-run it as a regression gate.

If there is no existing codebase: a Vite + React + TypeScript SPA (or Next.js if you want SSR
for the marketing sites) maps most directly onto this structure. One shared `ui/` package = the
kit; one app per site (or one app with sub-domains).

---

## 7. Where to look
- `README.md` — family overview & file map. `HANDOFF.md` — shared-layer contract, route maps,
  migration status (§8), open items.
- `MARKETING.md` — positioning + copy per brand. `CLAUDE.md` — repo rules (read it).
- `POSITIONING-AUDIT.md` — category-language alignment (context-engineering), marketing-vs-backend
  language map, and the OSS **competitive** landscape (Baltor §5 · Teleon §6).
- `BACKEND-STACK.md` — OSS **backend** building blocks per site (Sigstore · SLSA · CycloneDX
  AI-BOM · OpenSSF Scorecard · MCP registry · lm-eval-harness · LLMLingua).
- `EXPERIMENTS.md` — the shared A/B + tracking engine.
- `Design Acceptance Scorecard.html` — the consistency gate (10 criteria × 7 sites).
- `UX-BACKLOG.md` — prioritized net-new UX opportunities.
- Per-folder `README.md` — file map for each site. `openharnesshub/PAGES.md` — OHH routes.

## 8. Known open items (honest state)
- Accessibility: focus-visible is already shared in `oh-components.css`; a formal AA-contrast
  audit + 44px-target sweep is still owed (prototype-level only). This is the lowest Scorecard
  row (criterion 9, Partial family-wide) — the main thing left to lift the score.
- A few brand nav labels / CTA strings are still inline in JSX (not yet centralized in
  `products.js`) — optional consolidation.
- Everything else on the Scorecard is Pass (family score 94%). Re-run it after any change.
