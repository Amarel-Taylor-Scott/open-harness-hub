# SYSTEM INVENTORY — everything that already exists (DO NOT REBUILD)

**Machine-checkable manifest of every surface, module, export, experiment, and theme key.**
Before writing ANY new component, page, hook, or utility: search this file. If it exists
here, you port/reuse it — re-implementing anything on this list is a DESIGN-CONTRACT
violation (Rule 9). This file is generated from source; when in doubt, the source wins.

---

## 1. Surfaces — 24 total (own none? you missed some)

**Reconcile your build plan against this list. The count is 24.**

| # | Surface | Status | Folder / entry |
|---|---|---|---|
| 1 | AI Done Right (parent portfolio) | live | `context-is-everything/Context is Everything.html` |
| 2 | Demo Control Tower (operator console) | internal | `context-is-everything/Demo Control Tower.html` |
| 3 | Baltor.ai (context assurance, paid) | live | `context-enrichment/Context Enrichment Prototype.html` |
| 4 | Teleon.dev (purpose-driven runtime) | live | `teleon/Teleon Prototype.html` |
| 5–13 | 9 LIVE hubs: OpenContextHub · OpenSkillsHub · OpenToolsHub · OpenSkillToTool · OpenHarnessHub · OpenMCPHub · OpenCompressionHub · OpenBenchmarkHub · OpenReviewHub | live | `open*hub/<Name> Prototype.html` |
| 14–24 | 12 PRIVATE-BENCH hubs: OpenTemplatesHub · OpenEndpointHub · OpenEnvHub · OpenSandboxHub · OpenAgentHub · OpenReceiptHub · OpenStateHub · OpenReconciliationHub · OpenHardeningHub · OpenEnrichmentHub · OpenOptimizationHub · OpenVerificationHub | **private** | `open*hub/<Name> Prototype.html` |

Also internal (kit-based, no public domain): `inference-gateway/Shared Inference Gateway.html`,
`template-registry/Shared Template Registry.html`.

Source of truth: `shared/products.js` → `PORTFOLIO.ENTITIES` (23 entities) + `LAYERS`.
Statuses: 11 `live` + 12 `private`. The accent resolver maps `private` → muted accent +
"Private preview" banner; `live` → saturated accent, no banner.

## 2. Shared modules and their FULL export surface

### `shared/oh-site.jsx` — site kit (39 window exports — ALL exist, reuse them)
Hooks/util: `useHashRoute` `navigate` `useSiteTheme` `useExperiment`
Chrome: `OhLogo` `OhThemeToggle` `OhTopBar` `OhPortfolioMenu` `OhAppShell` `OhFooter`
Skeletons: `OhHero` `OhSection` `OhFeatures` `OhBand` `OhPageHead` `OhRollup`
**Account/auth pages (the "backend-facing" flows — these exist for every site):**
`OhAuth` (signin + signup + forgot) `OhDashboard` `OhApiKeys` `OhTeam` `OhAuditLog`
`OhBilling` `OhUsage` `OhSettings` `OhSwitch` `OhNotifications` `OhOnboarding`
Content pages: `OhDocs` `OhPricing` `OhContact` `OhAbout` `OhStatus` `OhChangelog`
`OhLegal` `OhNotFound` `OhCaseStudies` `OhCaseStudy`
Overlays: `OhCommandK` (⌘K palette) `OhExperimentsPanel` (A/B dev panel)

### `shared/oh-hub.jsx` — `makeHub(cfg)` registry engine (renders 21 complete sites)
Recognized config keys (all in use):
`brand{name,tld,glyph,accent}` `kind` `themeKey` `noun` `nounPlural` `indefinite`
`heroTitle` `lede` `ledeVariants{A,B,C}` `howTitle` `howBody` `features` `facets`
`standards` `trust(e)` `installCmd(e)` `entries[]` — and the gated hooks:
`entryExtra(e,helpers)` `extraRoutes[]` `convert{…,render}` `access:'private'` `openTrigger`.
Routes rendered PER HUB: `/` `/browse` `/e/:id` `/cases` `/cases/:id` `/docs` `/pricing`
`/about` `/status` `/changelog` `/terms` `/privacy` `/contact` `/dashboard` `/installed`
`/publish` `/keys` `/team` `/audit` `/notifications` `/billing` `/usage` `/settings`
`/signin` `/signup` `/forgot` (+ per-hub extraRoutes; OpenSkillToTool adds `/architecture` `/api` `/convert`).

### `shared/oh-experiments.js` — A/B engine (THIS EXISTS — do not write a new one)
API (`window.OHExp`): `define(key, variants, opts)` · `variant(key)` (sticky per-visitor) ·
`assign(key, id)` (force) · `clear(key)` · `track(event, props)` (auto-attaches all active
assignments, pushes to `window.dataLayer` with `_src:'oh-exp'`, caps 250 events) ·
`exposure(key)` (deduped impressions).
Persistence: localStorage `oh-exp-vid` / `oh-exp-assign` / `oh-exp-events`.
URL forcing: `?exp=key:Variant,key2:Variant`. React side: `useExperiment(key, variants)`
hook + `OhExperimentsPanel` (on every makeHub page).

**Active experiment keys (all must ship):**
- Engine-generated per hub (× 21 hubs): `<hubname>_landing` (`default`/`trust-first` layout)
  and `<hubname>_subhead` (A/B/C — every hub's `ledeVariants`, copy verbatim).
- Bespoke: `teleon_hero` (A–D) · `teleon_landing` · `baltor_hero` · `baltor_subhead` (A–D) ·
  `baltor_cta` (A–D) · `baltor_landing` · `ohh_hero` (A/B) · `ohh_subhead` (A–C).

### `shared/products.js` — brand registry (single source of identity)
`BRAND` (AI Done Right) · `GROUP` · `PORTFOLIO.ENTITIES` (23: 2 products + 21 hubs, each
with `name/wordmark/domain/kind/blurb/accent/glyph/url/status` and, for private:
`futureAccent/source/openTrigger`) · `LAYERS` (Platform / Open resources / Private bench)
· the **accent resolver** (status-aware: private → muted now, futureAccent on flip).

### Theme / light-dark infrastructure (EXISTS on every surface)
`useSiteTheme(themeKey)` + `OhThemeToggle`; root class `oh dir-s theme-{light|dark} oh-site`;
all tokens resolve per theme in `oh-tokens.css`; `--accent-weak` is translucent so hue
survives both themes. **Per-site localStorage theme keys (24 distinct, keep them):**
`teleon-theme`, Baltor + OHH + parent keys (see each main file), and per hub:
`och- osh- oth- os2t- omcp- ocmp- obm- orh- otpl- oep- oenv- osbx- oag- orc- ost- orec-
ohard- oenr- oopt- over-` + `theme`.

### Other shared
`shared/cases.js` (case studies keyed by hub name) · `shared/oh-tokens.css` (ALL color/
type/spacing tokens, both themes) · `shared/oh-components.css` (`.oh-card` `.oh-btn`
`.oh-badge` `.oh-input` focus rings, a11y floors) · `shared/oh-site.css` (`ohs-*` chrome) ·
`shared/oh-hub.css` (`ohub-*` + private-preview banner).

### Bespoke site code (exists; attaches to the kit, never replaces it)
`context-is-everything/cie-main.jsx` (+`cie.css`) · `context-enrichment/ce-*.jsx` (+css; Baltor
`dir-d` chrome) · `teleon/teleon-main.jsx` · `openharnesshub/proto-*.jsx` (+`PAGES.md`, ~43
routes) · `openskilltotool/os2t-pages.jsx` (+`os2t.css`) · `openreviewhub/orh-pages.jsx`
(+`orh.css`) · `Design Acceptance Scorecard.html` · `Demo Control Tower.html`.

---

## 3. Recognition gate (run BEFORE writing any code — DESIGN-CONTRACT Rule 9)

Produce and print this reconciliation table. **On a mismatch, don't halt — sweep the entire
repo, resolve from source (the repo is truth; this manifest is the index), log the
discrepancy in `PARITY-REPORT.md`, and proceed from the most complete design + backend spec
found:**

| Check | Expected | You found |
|---|---|---|
| Surfaces (entities + parent + tower) | 24 | ? |
| `PORTFOLIO.ENTITIES` count | 23 | ? |
| Hubs rendering from ONE makeHub | 21 | ? |
| `status:'private'` entities | 12 | ? |
| oh-site.jsx window exports | 39 | ? |
| Experiment engine API methods | 6 (define/variant/assign/clear/track/exposure) | ? |
| Bespoke experiment keys | 8 | ? |
| Per-hub experiment keys | 42 (21×landing + 21×subhead) | ? |
| Theme: per-site localStorage keys | 24 | ? |
| Kit CSS files to copy verbatim | 4 shared + per-site | ? |
