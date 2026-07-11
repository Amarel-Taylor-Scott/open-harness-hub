# OpenHubForAI — Implementation Handoff & Inventory

> Single source of truth for building the product in one go. The prototype
> (`OpenHubForAI.html`) is the functional spec; the exploration
> canvas (`index.html`) is the design-decision record (9 schemes × all artifacts).
> Scheme **S · Harness House** is the recommended locked direction.

---

## 0. Verification status (last full sweep)

All routes render their key element — **0 failures** (sweep: 2026-05). The canonical
route → purpose map lives in **`PAGES.md`**; the router itself (`proto-main.jsx`,
`App()`) is the source of truth. Highlights since the original 23-route sweep:

- **Explore split** into `/pipelines` (lift shown) + `/components` (no lift), each a
  `PBrowse` instance keyed by `kind`.
- **Modality tabs** on `/pipelines`: Text · Image · Audio · Video — 4 pipelines each
  (`COMPONENTS[].modality`, default `'text'`).
- **Tweaks** (text-size · density · intensity) in the bottom-left switcher → root
  classes `tw-text-{sm,lg}` · `tw-dens-{compact,comfortable}` · `tw-int-{calm,vivid}`,
  persisted to `localStorage('ohp-tweaks')`.
- **Legacy redirects** (IA cleanup): `/browse → /components`, `/marketplace → /pipelines`,
  `/explore → /pipelines` (the `REDIRECTS` effect in `App()`). `PMarketplace`/`PExplore`
  components were retired — Marketplace folded into the **Source** filter, Explore into the
  two Explore tabs.

---

## 1. File inventory

**Shared design layer (used by BOTH canvas + prototype)**
| File | Role |
|---|---|
| `oh-tokens.css` | 9 scheme token sets × light/dark (`.oh.dir-{s,a,b,c,d,e,f,g,h}.theme-{light,dark}`) |
| `oh-components.css` | shared atoms: buttons, badges, chips, cards, flow nodes + wiring, legend, comparison, accessibility base |
| `oh-explorations.css` | palette card, builder studies, diagram studies, library, batch, lift-evidence, system-states, scheme-switcher chrome |
| `oh-artifacts.jsx` | `PRIMS` (seven-primitive data), `FlowCanvas`, `Landing`, `BuilderResults`, `ComponentCard` (canvas) |

**Prototype layer**
| File | Exports |
|---|---|
| `proto.css` | app shell, marketing shell, drawer, palette, toasts, page layouts, modality tabs, tweaks classes, responsive |
| `proto-deep.css` / `proto-byo.css` / `proto-admin.css` / `proto-sdg.css` / `proto-value.css` / `proto-ops.css` / `proto-wide.css` | per-surface styles |
| `proto-store.jsx` | `COMPONENTS` (incl. multi-modal pipelines), `BY_SLUG`, `MODALITIES`, `PFLOW`, `ALTS`, `useHashRoute`, `navigate`, `StoreCtx`, `CompCard`, `liftBadge`, `provBadge`, `EXEC_COLOR`, `COST_LABEL`, `FLAGS`, `useFlag` |
| `proto-pages-build.jsx` | `PLanding` (modality-tabbed examples), `PBuild`, `PResults`, `PFlow`, `PRun`, `PPreview`, `Mark` |
| `proto-catalog.jsx` | `PBrowse` (faceted + modality tabs + zero-result), `PDetail`, `PDashboard`, `PNotFound`, `PPricing` |
| `proto-deep.jsx` | `PFoundry`, `PImprove`, `PDashboards`, `PSettings`, `CompConfig` |
| `proto-byo.jsx` | `PRegistry`, `PConnect` (MCP) |
| `proto-admin.jsx` | `PAdmin`, `PCheckout`, `PWorkers` |
| `proto-sdg.jsx` | `PSolutions`, `PSolution` |
| `proto-value.jsx` | `PFreshness`, `PAttest` |
| `proto-ops.jsx` | `PStatus`, `PActivity`, `PSources` |
| `proto-wide.jsx` | `PRequests`, `PRequestDetail`, `PContribute`, `PKnowledgeEntry`, `PProvenance`, `PTrustCenter`, `PAuditLog`, `PRoles`, `PSignin`, `POnboarding`, `PUpgrade` |
| `proto-pub.jsx` | `PPublish` |
| `proto-landings.jsx` | `PUseCase` (`/for/:who`) |
| `proto-main.jsx` | `App`, router + `REDIRECTS`, `AppShell`, `MarketingShell`, `Sidebar`, `Topbar`, `CommandPalette`, `Toasts`, `SchemeSwitcher` (+ Tweaks), `NAV_GROUPS`, `CMDS` |

---

## 2. Route map → component → shell → theme

`PAGES.md` is the canonical route → purpose map. This table is the
component / shell / theme binding (see `App()` in `proto-main.jsx`).

| Route | Component | Shell | Theme |
|---|---|---|---|
| `/` | PLanding | marketing | light |
| `/pricing` `/trust` | PPricing · PTrustCenter | marketing | light |
| `/signin` `/signup` `/onboarding` `/upgrade` `/preview` | PSignin · POnboarding · PUpgrade · PPreview | minimal | light |
| `/for/:who` | PUseCase | marketing | light |
| `/build` `/results` | PBuild · PResults | app | dark |
| `/flow` | PFlow (+inspector) | app (bare) | dark |
| `/run` | PRun | app | dark |
| `/pipelines` `/components` `/c/:slug` | PBrowse(pipeline) · PBrowse(component) · PDetail(+CompConfig) | app | dark |
| `/app` `/drafts` | PDashboard | app | dark |
| `/dashboards` `/foundry` `/improve` | PDashboards · PFoundry · PImprove | app | dark |
| `/registry` `/connect` | PRegistry · PConnect | app | dark |
| `/workers` `/freshness` `/attest` | PWorkers · PFreshness · PAttest | app | dark |
| `/solutions` `/solutions/:n` | PSolutions · PSolution | app | dark |
| `/activity` `/status` `/sources` | PActivity · PStatus · PSources | app | dark |
| `/requests` `/requests/:id` `/contribute` | PRequests · PRequestDetail · PContribute | app | dark |
| `/publish` `/audit-log` `/roles` | PPublish · PAuditLog · PRoles | app | dark |
| `/k/:id` `/p/:id` | PKnowledgeEntry · PProvenance | app | dark |
| `/admin` `/checkout` | PAdmin · PCheckout | app | dark |
| `/settings` | PSettings (5 sections) | app | dark |
| `*` | PNotFound | minimal | — |
| `/browse` → `/components`; `/marketplace` `/explore` → `/pipelines` | (legacy redirects) | — | — |

Routing = hash (`#/route`), `useHashRoute()`. Theme = route-based (marketing light / app dark) with a global override (scheme switcher), persisted to `localStorage` + `prefers-color-scheme`.

---

## 3. Shared primitives & tokens

**Seven-primitive legend** (`PRIMS`, the product spine): Input `⌖` · Knowledge Corpus `⛁` · Conditional `◈` · Action `⚡` · Loop/Flow `↻` · Stop `⊘` · Output `⎘` + Operator `◇`. Hues are tokens (`--p-input … --operator`), re-tuned per scheme, darkened for light themes. **Flow stage order: Input → Conditional → Knowledge → Action → Loop → Output.**

**Token contract** (set by each scheme scope; everything else uses `var()`): surfaces `--bg --bg-subtle --panel --panel-2 --line --line-strong`; text `--fg --fg-muted --fg-faint`; brand/semantic `--accent --accent-ink --accent-weak --success --warning --danger --info --verified`; primitives `--p-* --operator`; type `--font-display --font-sans --font-mono`; radius `--r-sm --r-md --r-lg --r-pill --r-node`; elevation `--e1 --e2`; motion `--ease`.

**Adding a scheme** = one CSS block. **Adding a primitive** = one `PRIMS` entry. **Adding a page** = one component + one router case + one `NAV`/`CMDS` entry.

---

## 4. Shared CSS class groups

- **Atoms (`oh-*`)**: `oh-btn(--primary/--ghost/--sm)`, `oh-badge(--lift/--verified/--warn/--danger/--muted/--stable)`, `oh-execdot`, `oh-comp-card` + `oh-cc-*`, `oh-minidag`/`oh-mininode`, `oh-fnode` + flow wiring (`oh-flow-svg`, `oh-fop`, `oh-flbl`), `oh-legend-*`, `oh-trace-*`, `oh-lift-*`, `oh-state*` (skeleton/empty/blocked/error/toast), `oh-result-*`.
- **App chrome (`pt-*`)**: `pt-shell/pt-side/pt-navitem`, `pt-topbar/pt-crumb/pt-cmdk`, `pt-page`, `pt-drawer`, `pt-cmdk-*` (palette), `pt-toast`, `pt-mkt-*` (marketing), `pt-hero/pt-entry/pt-chip`.
- **Per-surface (`pt-*`)**: `pt-funnel/pt-rejlog` (foundry), `pt-finding/pt-delta/pt-twin` (improve), `pt-widget/pt-spark` (dashboards), `pt-settings/pt-switch/pt-seg/pt-keyinput` (settings), `pt-config/pt-override/pt-ver` (deep config), `pt-bridge/pt-mcpnode` (connect), `pt-sdg-*`, `pt-fresh-src/pt-cdc-row/pt-sla` (freshness), `pt-cert/pt-seal/pt-prov-row` (attest), `pt-table/pt-quota` (admin), `pt-checkout/pt-summary` (checkout), `pt-worker/pt-wlog` (workers).

---

## 5. Shared components (reuse, don't re-author)

`Mark` (wordmark glyph) · `GFrame` (scheme+theme wrapper) · `AppShell`/`MarketingShell`/`Sidebar`/`Topbar` · `CommandPalette` · `Toasts` · `SchemeSwitcher` · `CompCard` · `Strip` (mini-DAG) · `Spark` (sparkline) · `Switch` · `liftBadge`/`provBadge`.

---

## 6. Designed states (every surface)

Empty (teach next action) · loading (skeleton shimmer) · blocked-by-gate (unproven lift / unsourced provenance, with reason + fix) · error (recoverable + retry) · success (toast) · simulate banner · zero-result→capability-request · near/over quota (admin). Live demo: `/states`-style coverage on the canvas + per-page (run error+retry, browse zero-result, detail blocked).

---

## 7. Data shapes to formalize (backend)

```
Component   { slug, primitive, type, name, desc, lift|null, liftClass?,
              cost('$'|'$$'|'$$$'|'⌂'), recurring:bool, prov('sourced'|'unsourced'|'verified'),
              license, lifecycle, exec('static'|'text'|'code'), industry, fresh?,
              modality('text'|'image'|'audio'|'video', default 'text') }
              // derived at load: kind('pipeline'|'component'), owner(source tier)
FlowNode    { id, primitive, slug?, name, ref(mono id), facts, lift?, x, y }   // + edges[], operator nodes, loop edges
PipelineObject (run artifact) { steps[{ primitive, ref, model:bool, tokens, cost, ms, status }],
                                totals{ cost, tokens, wall, citations }, simulate:bool }
Attestation { flow, sourcedAsOf, validThrough, factsCited, signature(C2PA), standard[] }
KnowledgeFact { id, corpus, content, source_url, author, license, lastVerified, triggers[], revoked:bool }
Tier        { tier, dag[], lift, components, packs, gov, cost, latency, freezablePct }
```

---

## 8. A/B testing & alternative pages (toggle on/off, wire later)

A lightweight **variant/flag layer** is scaffolded in `proto-store.jsx`:

```js
// defaults; overridden by ?flags=heroVariant:B,resultsLayout:table  or  localStorage 'ohp-flags'
const FLAGS = { heroVariant: 'A', resultsLayout: 'cards', pricingVariant: 'A' };
useFlag('heroVariant')  // → 'A' | 'B'   (currently the only wired flag — see PLanding)
```

The URL parser expects **`key:val`** pairs (`?flags=heroVariant:B`); a bare key sets `true`.
`resultsLayout` / `pricingVariant` are reserved defaults, not yet consumed.

Pattern to add an alternate page/variant **without forking the router**:
1. Author the alternate component (e.g. `PResultsTable`).
2. In the page, branch: `useFlag('resultsLayout') === 'table' ? <ResultsTable/> : <cards/>`.
3. Toggle via URL (`?flags=resultsLayout:table`), `localStorage('ohp-flags')`, or a server flag later.

This means marketing can run `/` hero A vs B, `/results` cards vs matrix, `/pricing` layout A vs B, etc., all behind flags — enable per-cohort when the experiment platform is wired. Keep both versions in the tree; the flag decides.

---

## 9. Open-spec vs governed boundary (build notes)

**Open (Apache-2.0, free):** spec/schemas, seven-primitive grammar, `oh-hub` CLI, reference SDK, export emitters (SPDX/C2PA/JSON-LD/EU-AI-Act), build & export, simulate. **Governed (subscription):** vetted components, live knowledge corpora (CDC freshness + revocation), build-on-demand, governance/review, attestation renewal. Runtime enforcement: exported flows phone home with metered, scoped credentials for governed retrieval; static/text-op steps are freezable.

## 10. Engineering workstreams (not screens)
Run orchestrator (single-call core + map-over-list batch) · priority job queue (paid>trial, per-tenant concurrency = anti-scrape lever, DLQ, retries, circuit-breakers) · sandboxed worker fleet + internet workers · CDC pipeline · measurement engine (decay) · cache · pgvector · signing/key infra (C2PA) + canary registry · metering→billing (Stripe) + credits ledger · secrets vault · tenant isolation · SOC2/GDPR.

## 11. Remaining work for completeness
Built since the original list: onboarding (`/onboarding`), auth (`/signin`/`/signup`), capability-request board (`/requests`), contribute (`/contribute`), upgrade paywall (`/upgrade`), knowledge-entry (`/k/:id`), activity feed (`/activity`), status (`/status`), trust center (`/trust`).

Still stubbed or unbuilt (currently route to the 404 via `/nope`): **Docs**, legal pages (terms / privacy / DPA), SSO·SCIM provisioning, alert-rule editor on `/activity`, and first-run product tour. Marketplace + scale-`/explore` were intentionally retired (folded into the Source filter + the two Explore tabs).
