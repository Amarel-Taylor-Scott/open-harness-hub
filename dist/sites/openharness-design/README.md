# AI Done Right — Brand Family Prototypes

> **Implementing this in a real codebase?** Start with **`START-HERE-CLAUDE-CODE.md`** — a
> paste-ready Claude Code kickoff prompt, the reading order, and the prototype→production gap.

High-fidelity, interactive **design prototypes** for the AI Done Right portfolio: a
platform company with two governed products and a large family of open registries, all on
one shared design system. These are design artifacts (a precise spec to implement against),
**not** production code — see [Prototype vs. production](#prototype-vs-production).

> **Brand:** the company is **AI Done Right** (`aidoneright.dev`), tagline **"AI, done
> right."** Thesis across every property: **discovery is not trust** — take open,
> discoverable AI building blocks and turn them into governed, evidence-backed capability.
> The platform is the company; the `OpenHubForAI` sites are the open, top-of-funnel lead-gen.

> ⚠️ **Legacy paths, current brand.** Folders/files keep their original names
> (`context-is-everything/Context is Everything.html`, repo root `openharness/`) so the
> ~20 cross-links in hub footers + the Control Tower don't break. The *displayed* brand is
> "AI Done Right" everywhere (driven by `products.js`). Paths are invisible to users; don't
> rename them without sweeping every `../context-is-everything/...` reference.

```
AI Done Right                        platform company / portfolio   context-is-everything/
  Products (governed, paid)
    ├── Baltor.ai                    context assurance              context-enrichment/
    └── Teleon.dev                   purpose-driven runtime         teleon/
  Open network (live, open funnel)   9 registries via makeHub()
    ├── OpenContextHub.io  · OpenSkillsHub.io · OpenToolsHub.io
    ├── OpenSkillToTool.io · OpenMCPHub.io · OpenCompressionHub.io
    └── OpenBenchmarkHub.io · OpenReviewHub.io · OpenHarnessHub.io
  Private bench (built, status:'private') 12 registries via makeHub()
    ├── OpenTemplatesHub.io · OpenEndpointHub.io · OpenEnvHub.io
    ├── OpenSandboxHub.io · OpenAgentHub.io · OpenReceiptHub.io · OpenStateHub.io
    └── context-governance method hubs (Baltor engine spine):
          OpenReconciliationHub.io · OpenHardeningHub.io · OpenEnrichmentHub.io ·
          OpenOptimizationHub.io · OpenVerificationHub.io
shared/                             design system + site kit + brand registry
```

A *branded house*: identical type scale, spacing, primitives, fonts, chrome and dark-mode
mechanism — **only the accent color differs**. Live hubs carry saturated accents; private
bench hubs render a **muted** accent + a "Private preview" banner until they open.

## Open each site
| Site | Status | Accent | Entry file |
|---|---|---|---|
| AI Done Right (parent) | — | blue | `context-is-everything/Context is Everything.html` |
| Baltor.ai | live | `#0e7c86` | `context-enrichment/Context Enrichment Prototype.html` |
| Teleon.dev | live | `#6d5ef0` | `teleon/Teleon Prototype.html` |
| OpenContextHub | live | `#2f8f6b` | `opencontexthub/OpenContextHub Prototype.html` |
| OpenSkillsHub | live | `#2f7d8f` | `openskillshub/OpenSkillsHub Prototype.html` |
| OpenToolsHub | live | `#8f6f2f` | `opentoolshub/OpenToolsHub Prototype.html` |
| OpenSkillToTool | live | `#cf5a96` | `openskilltotool/OpenSkillToTool Prototype.html` |
| OpenMCPHub | live | `#5b7cf0` | `openmcphub/OpenMCPHub Prototype.html` |
| OpenCompressionHub | live | `#9bd61f` | `opencompressionhub/OpenCompressionHub Prototype.html` |
| OpenBenchmarkHub | live | `#e0556a` | `openbenchmarkhub/OpenBenchmarkHub Prototype.html` |
| OpenReviewHub | live | `#9d4edd` | `openreviewhub/OpenReviewHub Prototype.html` |
| OpenHarnessHub | live | `#d2542f` | `openharnesshub/OpenHarnessHub Prototype.html` |
| OpenTemplatesHub | **private** | `#6d6a86`→`#7c5cff` | `opentemplateshub/OpenTemplatesHub Prototype.html` |
| OpenEndpointHub | **private** | `#5f7585`→`#1f8fd6` | `openendpointhub/OpenEndpointHub Prototype.html` |
| OpenEnvHub | **private** | `#5f7a6e`→`#2f9e5a` | `openenvhub/OpenEnvHub Prototype.html` |
| OpenSandboxHub | **private** | `#7a6f86`→`#b5562f` | `opensandboxhub/OpenSandboxHub Prototype.html` |
| OpenAgentHub | **private** | `#7a7460`→`#0f9e8e` | `openagenthub/OpenAgentHub Prototype.html` |
| OpenReceiptHub | **private** | `#72786b`→`#c79a2e` | `openreceipthub/OpenReceiptHub Prototype.html` |
| OpenStateHub | **private** | `#6c6f86`→`#0ea5a5` | `openstatehub/OpenStateHub Prototype.html` |
| OpenReconciliationHub | **private** | `#6a7080`→`#2f6fae` | `openreconciliationhub/OpenReconciliationHub Prototype.html` |
| OpenHardeningHub | **private** | `#7a6f6a`→`#b5562f` | `openhardeninghub/OpenHardeningHub Prototype.html` |
| OpenEnrichmentHub | **private** | `#6a7a72`→`#2f9e7a` | `openenrichmenthub/OpenEnrichmentHub Prototype.html` |
| OpenOptimizationHub | **private** | `#76707f`→`#c8902f` | `openoptimizationhub/OpenOptimizationHub Prototype.html` |
| OpenVerificationHub | **private** | `#6f7a80`→`#1f9b8e` | `openverificationhub/OpenVerificationHub Prototype.html` |

(`muted`→`launch` accents: a private hub stores both; the launch color is adopted on open.)
Just open the HTML in a browser — no build step. Each folder has its own `README.md`.

## Tech shape (all sites)
- Plain HTML + **React 18 via in-browser Babel** (`<script type="text/babel">`). Pinned
  CDN versions with integrity hashes (copy them exactly from any hub's HTML).
- Hash routing (`#/route`). No router lib (`useHashRoute`/`navigate` in the kit).
- Each Babel file gets its own scope; cross-file sharing is via `Object.assign(window, {…})`.
- All styling flows from `shared/` tokens. **Never hardcode a hex** in a site stylesheet.
- Mock data only. No network calls, no backend.

## Shared foundation — `shared/`
- **`oh-tokens.css`** — all color/space/radii/shadow/type tokens, scoped
  `{dir-d|dir-s} × {theme-light|theme-dark}`. Source of truth for every color.
- **`oh-components.css`** — canonical primitives + scale vars. `.oh-card`, `.oh-btn`,
  `.oh-badge`, `.oh-tabs`, `.oh-table`, `.oh-segment`, `.oh-field`, `.oh-input`,
  `.oh-switch` + scale (`--fs-*`, `--pad-*`, `--h-topbar`, `--maxw-site`).
  **Change a primitive here → every site updates.**
- **`oh-site.css` + `oh-site.jsx`** — the **SHARED SITE KIT**. Chrome (`OhTopBar`,
  `OhAppShell`, `OhFooter`), skeletons (`OhHero`, `OhSection`, `OhFeatures`, `OhBand`,
  `OhPageHead`, `OhRollup`), **primitive pages** (`OhAuth`, `OhContact`, `OhPricing`,
  `OhBilling`, `OhUsage`, `OhSettings`, `OhDashboard`, `OhApiKeys`, `OhTeam`,
  `OhAuditLog`, `OhDocs`, `OhAbout`, `OhStatus`, `OhChangelog`, `OhLegal`,
  `OhNotFound`, `OhCaseStudies`/`OhCaseStudy`), the `OhCommandK` palette, and hooks
  `useHashRoute` / `navigate` / `useSiteTheme`. A new brand sets ONE `--accent` and inherits
  all of it.
- **`oh-hub.css` + `oh-hub.jsx`** — **`makeHub(cfg)`**: an entire open-registry site
  (landing + browse graph + entry detail + the full account console) from a single config
  object. **All 21 OpenHubForAI registries are config-only.** See [makeHub config](#makehub-the-registry-engine).
- **`products.js`** — **single source of truth for brand + portfolio.** `window.BRAND`,
  `window.PRODUCTS`, `window.PORTFOLIO` (`GROUP`/`ENTITIES`/`LAYERS`/`PORTS` — drives the
  parent). **Renames are one-line edits.** Also runs the [flip-to-public](#private-first--flip-to-public)
  accent resolver.
- **`cases.js`** — case-study content per brand (`window.CASES[brandId]`), rendered by the
  kit's `OhCaseStudies`/`OhCaseStudy`; every site has `/cases` + `/cases/:id`.
- **`oh-experiments.js`** — the shared A/B + tracking engine (`window.OHExp` /
  `useExperiment`). See `EXPERIMENTS.md`.

## makeHub — the registry engine
A hub is a config object. Core keys: `brand {name,tld,glyph,accent}`, `kind`, `themeKey`,
`noun`/`nounPlural`/`indefinite`, `heroTitle`, `lede` (+`ledeVariants` for A/B), `howTitle`,
`howBody`, `features[[glyph,title,desc]]`, `facets[]`, `installCmd(e)`, and
`entries[{id,name,by,facet,desc,installs,score,ver,deps?}]`. Optional: `standards[[name,desc]]`
and `trust(e)` to override the provenance rows.

makeHub renders, per hub, the full site: marketing landing (hero + how + open-standards +
trust band), `/browse` graph with facets + search, `/e/:id` entry detail with a
provenance/trust rail, and the app console — `/dashboard /installed /publish /keys /team
/audit /notifications /billing /usage /settings`, plus `/docs /pricing /cases /about /status
/changelog /terms /privacy` and ⌘K.

### Config-gated extension hooks (added for OpenSkillToTool / OpenReviewHub)
These are **opt-in** — a hub that doesn't set them is unchanged:
- **`entryExtra(e, helpers)`** → extra cards on every entry-detail page. Used by
  OpenReviewHub (`orh-pages.jsx` → review report: artifact under review, axis scorecard,
  claim→evidence→verdict ledger) and OpenSkillToTool (`os2t-pages.jsx` → source skill,
  contract tabs, scope manifest, determinism/parity, fixtures).
- **`extraRoutes: [{path, navLabel, navIcon, render(helpers)}]`** → adds app routes + nav
  entries. OpenSkillToTool uses it for `/architecture` (backend pipeline) and `/api`.
- **`convert: {…, render(helpers)}`** → adds a `/convert` workbench (hero CTA + nav). When
  `render` is supplied it replaces the default workbench (OpenSkillToTool's multi-step wizard).
- **`access: 'private'` + `openTrigger`** → renders the pre-launch banner (see below).

Bespoke hub code lives in the **site folder** (e.g. `openskilltotool/os2t-pages.jsx` +
`os2t.css`, `openreviewhub/orh-pages.jsx` + `orh.css`), composed via these hooks — so the
shared kit stays generic and the other hubs are untouched.

## Private-first / flip-to-public
The 12 **private bench** hubs are fully built but `status: 'private'` in `products.js` (7
platform-substrate hubs + 5 context-governance **method hubs** that open Baltor's full engine
spine — Reconcile · Harden · Enhance · Optimize · Verify). The release policy is encoded, not
just documented:
- Each entity stores a muted **`accent`** (pre-launch) and a saturated **`futureAccent`**
  (launch), plus a `source` (modular component it's drawn from) and an `openTrigger`.
- `products.js` runs a resolver: for any entity with `futureAccent`, it keeps `privateAccent`
  + `launchAccent` and sets the effective `accent = status==='live' ? futureAccent : accent`.
- Each hub config derives `access: E.status === 'private' ? 'private' : undefined`, which
  gates makeHub's "Private preview" banner.
- **Opening a hub = a one-line change: `status: 'private' → 'live'`.** The muted accent
  swaps to the launch color and the banner disappears automatically — everywhere (parent
  portfolio, the hub itself, the Control Tower).

## Who's built on what
- **Teleon + all 16 hubs** — built ENTIRELY on the kit (`oh-site.jsx`; hubs via `makeHub`).
  Pure config; bespoke hub surfaces are folder-local files composed through the hooks above.
- **Baltor** — predates the kit; own router/chrome (`ce-*`), but its whole account layer
  renders via the SHARED KIT (`OhAuth`/`OhContact`/`OhSettings`/`OhBilling`/`OhUsage`/
  `OhAuditLog` inside Baltor's `AppShell`). Unique surfaces: the `/engine` lifecycle, Sources,
  Pipeline run, Verified corpora, Verify, Serve, Governance, Commons — plus static
  product-story pages (`.cd-*`) and 18 guided demos. See `CLAUDE-CODE.md §3.5`.
- **OHH** — oldest; keeps its `pt-*` product pages but consumes the kit for all chrome +
  account pages (`OhAppShell`/`OhSettings`/`OhAuditLog`/`OhAuth`/`OhTopBar`/`OhFooter`).
  `.pt-panel` is aliased to `.oh-card`.

## Branded-house guarantees (don't break)
1. Every card surface resolves to `.oh-card` (Baltor `.ce-*` + OHH `.pt-panel` compose it).
2. All sites load **Hanken Grotesk** as `--font-display`.
3. Size against the shared `--fs-*`/`--pad-*` vars, never raw px.
4. Per-site CSS adds *layout* only; never re-declares the shared surface/scale.
5. The parent overrides `dir-s` under `.oh.dir-s.cie` selectors — keep that specificity.
6. New kit brands set ONE inline `--accent`; `--accent-weak` is translucent so it keeps hue
   in light AND dark.

## Add a new site (~15 min, fully on-brand)
1. **A registry/hub** → copy a hub folder (e.g. `openreceipthub/`), swap the `makeHub({…})`
   config + the HTML's `<title>` and `-main.jsx` src, add the entity to `ENTITIES` +
   `LAYERS` in `products.js`. The parent portfolio + Control Tower pick it up from `PORTFOLIO`.
   For a private-first hub: set `status:'private'`, a muted `accent` + a `futureAccent`, an
   `openTrigger`, and `access: E.status==='private' ? 'private' : undefined` in the config.
2. **A product/app** → copy `teleon/`, swap the brand config + write unique pages; auth,
   billing, usage, settings, dashboard, docs come from the kit.

## Prototype vs. production
**Ready as spec:** every screen, flow, IA, interaction, copy line, and the full design
system — dark-mode clean, zero horizontal overflow, console clean (only the expected Babel
dev warning).

**A production build must add (absent by design):**
1. Real toolchain — Vite/Next with **precompiled JSX** (in-browser Babel is prototype-only).
2. Backend + API + datastore + the ingest/verification/engine pipeline (all mocked now).
3. Auth, persistence, billing (simulated).
4. Real data — all corpora / conflicts / runs / usage / registry entries are fixtures.

## Docs in this repo
- This file — family overview.
- `CLAUDE-CODE.md` — **start here for a developer/Claude Code handoff**: orientation, the
  site kit to port first, the prototype→production gap, and where everything lives.
- `MARKETING.md` — brand positioning + canonical marketing copy.
- `POSITIONING-AUDIT.md` — category-language alignment + the OSS competitive landscape.
- `BACKEND-STACK.md` — open-source backend building blocks (Sigstore · SLSA · CycloneDX
  AI-BOM · OpenSSF Scorecard · MCP registry · eval harnesses).
- `context-is-everything/Demo Control Tower.html` — operator "Start Here" console: every
  site, demo, dashboard, hub (incl. the Private Bench) and internal plane with URLs + status
  chips. Projection-only.
- `inference-gateway/Shared Inference Gateway.html` — internal LLM-plane console →
  `ModelInvocationReceipt`. Projection-only.
- `teleon/Teleon PurposeTask Control Tower.html` — staff console: CapabilityTask contract,
  candidate scorecard, promotion gates, `HumanApprovalReceipt`. Projection-only.
- `template-registry/Shared Template Registry.html` — internal template families.
- `HANDOFF.md` — implementation brief (shared-layer contract, route maps, rename points).
- `Design Acceptance Scorecard.html` — the branded-house consistency gate.
- `UX-BACKLOG.md` — prioritized net-new UX opportunities.
- `EXPERIMENTS.md` — the shared A/B + tracking engine.
- Per-folder `README.md` — file map for each site.
- `openharnesshub/PAGES.md` — OHH route catalog.
