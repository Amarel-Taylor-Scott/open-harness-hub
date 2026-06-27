# context-enrichment/ — Baltor.ai

The paid SaaS: **context assurance for AI agents** (brand name **Baltor**; the folder/key
is historically `context-enrichment`). Hash-routed React SPA + a docs subdomain surface.

Entry: **`Context Enrichment Prototype.html`** → open in a browser.

## Files (load order matters — see the HTML)
| File | Responsibility |
|---|---|
| `Context Enrichment Prototype.html` | Shell: loads React/Babel, fonts, shared CSS, then the JSX modules below. |
| `ce.css` | All Baltor-specific layout (`.ce-*`). Surfaces compose shared `.oh-card`; scale from shared `--fs-*`/`--pad-*`. |
| `ce-store.jsx` | Router (`useHashRoute`/`navigate`), mock data (corpora, conflicts, commons, publishers, reg-feed, artifacts), `useTheme`, `FLAGS`/`useFlag`. Brand atoms `TIER_META`, `STATUS_META`. |
| `ce-shell.jsx` | Brand chrome: `CEMark`/`CELogo`, `MarketingTop`, `AppShell` (sidebar), `ThemeToggle`, shared atoms (`StatusBadge`, `Meter`, `PageHead`). |
| `ce-landing.jsx` | Marketing site: `Landing` (hero/how/verify-moat/commons/tiers/serve/CTA) + `WhyPage`. |
| `ce-docs.jsx` | Docs subdomain: `DocsPage` with tabs Overview · Guides (10 articles) · Reference (glossary) · Demos (gallery + runner) · API (REST reference). |
| `ce-app.jsx` | Product app: Corpora, Ingest, CorpusDetail, Serve, Verify, Commons, Governance, Settings. |
| `ce-main.jsx` | App root: theme + route → renders marketing / docs / app chrome. Mounts `#root`. |

Each `.jsx` exports to `window` via `Object.assign` at its end; `ce-main` consumes them.

## Routes (hash)
`/` landing · `/why` · `/commons` (oracle marketplace) · `/docs` (subdomain: Overview/
Guides/Reference/Demos/API) · `/corpora` · `/ingest` · `/c/:id` corpus detail (Tiers/
Provenance/Serve/Compliance/Settings) · `/serve` console · `/verify` reconciliation queue ·
`/governance` · `/settings` · `/billing` · `/usage` · `/audit` · `/pricing` · unknown → NotFound.

**Account layer is now the SHARED KIT.** `/settings` (OhSettings), `/billing` (OhBilling),
`/usage` (OhUsage) and `/audit` (OhAuditLog) render the kit's Oh* pages (same components
Teleon + the hubs use), fed Baltor-specific content — Baltor's bespoke `ce-*` versions are
retired. They render inside Baltor's in-house `AppShell`, so chrome stays in-house while the
pages are kit. Auth (`/signin /signup /forgot`) + `/contact` already route through the kit.

## House style
- Scope `oh dir-d theme-{light|dark} ce-root`. Accent = teal (`--accent`).
- Display font Hanken Grotesk; mono IBM Plex Mono.
- Dark mode: `ThemeToggle` (top bar + sidebar), persisted `localStorage('baltor-theme')`.
- Hero A/B: runs on the **shared experiments engine** (`window.OHExp` / `useExperiment`,
  experiment key `baltor_hero`, **9 variants A–I** from `BRANDCE.hooks` — problem-, trust-,
  engine- and category-framed), plus `baltor_subhead` (A–E) and `baltor_cta`. Force with
  `?exp=baltor_hero:I` or the in-hero A/B pill; the hero CTA tracks a
  `cta_click` conversion and the `OhExperimentsPanel` is on the landing.
- Landing **layout** A/B: `baltor_landing` (`default` / `engine` / `problem` / `proof`) re-sequences
  the same sections into different narratives — see `LANDING_LAYOUTS` in `ce-landing.jsx`. Force
  with `?exp=baltor_landing:engine`. See `../EXPERIMENTS.md`. (`useFlag`/`setFlag` remain as thin
  back-compat shims that delegate to `OHExp`.)

## Positioning baked into copy (keep consistent)
Lead with **verification** (correct, not just current) · provenance/proof · tiers
(raw/compressed/hyper-efficient) · oracle-published Commons · serve into the agent you
already run. Lexicon: say **lean/efficient**, never "compression" as a headline; never
claim "100% accurate".

## Static product-story surfaces (`.cd-*` layer, `guided-demo.css`)
Beyond the React app, Baltor ships static narrative pages that sell the governed-context engine
(dir-d teal; load `../shared/oh-*` + `guided-demo.css`; tracked via `oh-experiments.js` + `track.js`):
- `Baltor Engine.html` — engine overview hub (4 pillars + 5-stage pipeline → deep-dives).
- 5 stage deep-dives — `Baltor Reconciliation/Anti-Fragility/Enhancement Deep-Dive.html`,
  `Baltor Optimization Showcase.html`, `Baltor Receipts Explorer.html`. Share `engine-stagenav.js`
  (one cross-stage nav; `mountStageNav('<key>')`). NOTE: on-surface the 02 stage reads **Hardening**;
  "anti-fragility" is the internal label only.
- `Baltor Guided Demos.html` — index of **18 worked demos** (`guided-demo.js` `SCENARIOS`); each is
  a 7-stage governed run that serves a verified answer + **holds the contradiction out**. Add a
  domain = one scenario object + thin shell HTML + index entry (in `Baltor Guided Demos.html` `META`).
- `Baltor Federal Register Coverage.html` (50 CFR titles, 11 demo-linked) · `Baltor International
  Coverage.html` · `Baltor Context Governance Report.html` · `Baltor Where It Fits.html` (OSS
  landscape). Receipts name the open standards (Sigstore·Rekor / in-toto / CycloneDX AI-BOM).

## Mock data → real API (for implementation)
All data is fixtures in `ce-store.jsx`. The docs **API** tab is the intended REST contract
(`/v1/corpora`, `/serve`, `/verify`, `/commons`, `/conflicts`, `/artifacts`). Wire these to
real services; replace `CORPORA`, `CONFLICTS`, `COMMONS`, `REG_CHANGES`, `ARTIFACTS`.
