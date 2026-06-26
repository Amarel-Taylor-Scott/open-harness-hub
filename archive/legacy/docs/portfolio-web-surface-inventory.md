> Superseded by `docs/DESIGN-BIBLE.md` (the live surface map). Kept as the dated 2026-06-09 inventory snapshot.

# Portfolio Web Surface Inventory — Operational web pages, views, routes, and primitives

> **⚠ SUPERSEDED for the LIVE surfaces (2026-06-26).** The live product surfaces are now ONE canonical
> scaffolding — `scripts/surface_server.py` → **5 surfaces** (AI Done Right · Teleon · Baltor · AIDevObserver ·
> OpenHubForAI), one byte-identical light/Inter design system, 5 URLs. Current truth: **`docs/DESIGN-BIBLE.md`**
> (the design reference) + `docs/CURRENT-STATE.md`. This file is kept for lineage as the historical 2026-06-09
> inventory of the earlier fragmented `web/` + `dist/sites/` surfaces (those fragmented systems are retired).

_Snapshot: 2026-06-09. This is the operational web/runtime inventory built by sweeping the repo (web/,
websites/, generated `dist/sites/`, scripts/baltor_admin_demo_server.py, scripts/portfolio_lib.py,
web/baltor/styles/, docs/concepts/). It is not the full AI Done Right design-family catalog. For the current
parent + Baltor + Teleon + 21 Open*Hub prototype bundle, use
`python3 scripts/check_ai_done_right_surface_family.py --self-test` and
`docs/design/openharness-claude-design/FAMILY-README.md`._

## How to read this

Status legend (verified against files, not aspiration):

- **LIVE** — wired to a real API/handler, works offline.
- **STATIC** — self-contained HTML (marketing/explainer), no backend.
- **PROJECTION** — read-only view over a real runtime; "computes no truth" (the governed pattern).
- **STUB** — page/route exists but the backing feature is candidate/placeholder.
- **TEMPLATE** — scaffolded + styled, route/JS not yet implemented.
- **GAP / NONE** — named in strategy but no UI/route exists.
- **LEGACY** — deprecated, kept as a redirect/compat shim.

Governance invariants every surface honors: dashboards are **projection-only** · **LLM output is candidate, never
served truth** · benchmark result ≠ promotion authority · candidate ≠ active · no raw secret values anywhere.

---

## 0. Surface map (at a glance)

| # | Website | Location | Kind | Status |
|---|---------|----------|------|--------|
| 1 | **Baltor** (app + demo) | `web/baltor/` + `scripts/baltor_admin_demo_server.py` | SPA + 33 page routes + 80 API routes | LIVE core / mixed |
| 2 | **AI Done Right** (HoldCo; founding thesis: ContextIsEverything) | `web/context-is-everything/` + `dist/sites/contextiseverything/` | parent-brand pages | BUILT |
| 3 | **Teleon.dev** | `websites/teleon.dev/` → `dist/sites/teleon.dev/` | one-pager | BUILT |
| 3b | **Teleon Control Tower** (staff) | — (`prompts/teleon-build-kit.md`) | greenfield TS | **NONE** |
| 3c | **Capability Assurance Portal** (customer) | — | greenfield TS | **NONE** |
| 4 | **OpenHarnessHub** | `web/harness-hub/` + `websites/openharnesshub/` + `catalog/` | product app + one-pager + catalog | one-pager BUILT / app TEMPLATE |
| 5 | **OpenContextHub** | `websites/opencontexthub/` → `dist/sites/` | one-pager | BUILT |
| 6 | **OpenSkillsHub** | `websites/openskillshub/` → `dist/sites/` | one-pager | BUILT |
| 7 | **OpenToolsHub** | `websites/opentoolshub/` → `dist/sites/` | one-pager | BUILT |
| 8 | **OpenMCPHub** | — | named only | **GAP** |
| 9 | **OpenCompressionHub** | — | named only | **GAP** |
| 10 | **OpenBenchmarkHub** | data: `catalog/benchmarks/`, `architecture/open_benchmark_registry.json` | named only | **GAP (no site)** |
| 11 | **Demo Control Tower** | `dist/sites/demo-control-tower/` | meta-index | BUILT |
| 12 | **Portfolio hub** | `dist/sites/portfolio/` | nav hub | BUILT |

---

## 1. BALTOR

### 1A. SPA routes (`web/baltor/app.js` + `pages/manifest.json`)

| Route | View file | Purpose | Status |
|-------|-----------|---------|--------|
| `/` | `pages/overview.js` | Landing: three-tier serving model (source ledger → verified context → serving packages), Context Engine hero, feature surfaces (MCP/API, RAG records, graph, audit packet) | LIVE |
| `/engine` | `pages/engine-hero.js` | Full-screen animated Context Engine — 6 macro stages + verification rail, reads `stages.json`, interactive hover detail | LIVE |
| `/pricing` | `pages/pricing.js` | Tiers: Assessment (free) · Processing (metered) · Serving packages (storage-priced) · Monitored context (recurring) | LIVE |
| `/trust` | `pages/trust.js` | Trust policy: fact-state lineage, multi-source adoption, source trust checks, reconciliation, archive/provenance, OHH discipline | LIVE |

Header external links: Live dashboard · Live demo · Review queue · Demo · How it works · Context is Everything · GTM guide · Open Harness Hub.

### 1B. Static / feature pages — every `web/baltor/*.html`

**Core ops (wired to /api):**

| Page | Title | Purpose | Status |
|------|-------|---------|--------|
| `dashboard.html` | Live Ops Dashboard | 7-stage board + live event stream + metrics (answer, lift, pack tokens, reviews) + artifacts; SSE+poll; "Run Full Pipeline"; links `/inference-plane`; renders inference.* as candidate-not-truth | LIVE |
| `demo-console.html` | Live Demo Console | Deterministic guided replay; corpus selector, 7 expanding stage cards, pack graph, lift bar, version lineage; `demo-run.json`/`demo-run.cfpb.json` | LIVE |
| `reviews.html` | Human Review Queue | Review tasks from `/api/review/queue` | LIVE |
| `hub.html` | Control Hub | Central nav: 4 ops cards + 7 context surfaces; polls dev status + events | LIVE |
| `raw.html` | Raw Feed | Ground-truth JSON: every bus event + flywheel status (poll) | LIVE |
| `dev-dashboard.html` | Dev Flywheel | Builder proof grid, flywheel ticks, dev timeline, backlog | LIVE |
| `fleet.html` | Live Supervisor Fleet | Live supervisor + worker fleet, claimed tasks, health | LIVE |

**Educational / explainer (static, no API):**

| Page | Title | Purpose | Status |
|------|-------|---------|--------|
| `how-it-works.html` | How Baltor works — sync, verify, reconcile, serve | Animated full-pipeline explainer; 6 stages + assurance engine + sources + watchers + delivery tiers; no external deps | STATIC |
| `context-engine-hero.html` | Context Engine Visual | Full-width animated canvas (stage flow) + 6-stage rail breakdown; offline | STATIC |
| `context-stages.html` | Context stages | Stage-language explainer (reads `stages.json`) | STATIC |
| `cfpb-artifact-graph.html` | CFPB Artifact Graph | Inspectable pipeline: ingest→source graph→decomposition→store→vectorize→deterministic graph→conflicts→reconciliation→receipt | STATIC |
| `temporal-graph.html` | Temporal Fact Graph | What was true / when valid / what superseded it; Reg E "10 business days" verified-current vs FAQ "30 days" held out; Graphiti = candidate | STATIC |
| `integrate.html` | Integrate CFPB data | Guided ingestion demo; links to hub/ops/raw/dev | STATIC |

**Projection-only feature pages:**

| Page | Title | Purpose | Status |
|------|-------|---------|--------|
| `inference-plane.html` | Shared LLM Plane (projection-only) | Provider graph, health, free-endpoint due-diligence, preference coverage, structured-local candidate box; model output never truth | PROJECTION |
| `memory.html` | Memory (candidate · projection-only) | Governed memory provider (candidate artifacts, profile, connectors, claim status, held-out); Supermemory = candidate | PROJECTION |
| `native.html` | Native Format Preservation (preview) | Paste JSON/CSV/MD → preview in original shape + governance sidecar + field-level diff; original never overwritten | PROJECTION |
| `determinism.html` | Determinism Factory (projection-only) | LLMs propose → Baltor verifies → consensus-as-evidence → mined rule → replay → shadow → promotion; CFPB rule reproduces "10 business days" | PROJECTION |
| `standards.html` | Standards System | Pattern registry, standards + template catalogs, routine library, waivers | PROJECTION |
| `consume.html` | Ingestion → Consumption | Product output: ContextResponse with served facts, held-out warnings, verification→optimization→consumption receipt lineage | PROJECTION |

**Stage deep-dives — `web/baltor/stages/` (all 6):**

| Page | Stage | Purpose | Status |
|------|-------|---------|--------|
| `stages/source.html` | 00 Source Systems | Raw ingress; preserves timestamps, permissions, hashes, source handles | STATIC |
| `stages/reconciliation.html` | 01 Reconciliation | Cluster alignment, dedupe, relationship mapping, contradiction surfacing | STATIC |
| `stages/anti-fragility.html` | 02 Anti-Fragility | Replaces brittle text with refreshable objects | STATIC |
| `stages/enhancement.html` | 03 Enhancement | Adds external context, metadata, architecture links | STATIC |
| `stages/optimization.html` | 04 Optimization | Summarize, distill, rank for task token budget | STATIC |
| `stages/consumption.html` | 05 Consumption | Serves task-specific packs with receipts + controlled expansion | STATIC |

**Pipeline journey — `web/baltor/pipeline/` (all 8):**

| Page | Title | Purpose | Status |
|------|-------|---------|--------|
| `pipeline/index.html` | Pipeline Journey | Walk one run stage by stage; held-out/rejected/source-handles + lineage | STATIC/PROJ |
| `pipeline/upload.html` | Upload & Ingestion | Ingest files, connect sources, preserve handles | STATIC/PROJ |
| `pipeline/decomposition.html` | Processing & Decomposition | Extract objects, chunk, parse, route (OCR, entities, claims, nodes, edges) | STATIC/PROJ |
| `pipeline/reconciliation.html` | Conflict & Reconciliation | Dedupe, link, surface contradictions across sources | STATIC |
| `pipeline/verification.html` | Verification Gate | Source role, publisher, stability, archive, markup, spam, injection-risk checks | STATIC |
| `pipeline/enhancement.html` | Enhancement | Enrich with external context, metadata, tools | STATIC |
| `pipeline/optimization.html` | Optimization (bake-off) | Rank, summarize, shape for token budget | STATIC/PROJ |
| `pipeline/consumption.html` | Consumption (served context) | Final ContextResponse: facts + held-out warnings + receipt lineage | STATIC/PROJ |

**Legacy:**

| Page | Purpose | Status |
|------|---------|--------|
| `oracle-hero.html` | Deprecated redirect → `context-engine-hero.html` ("Oracle" product language retired) | LEGACY |

**Config/data files:** `index.html` (SPA shell), `app.js` (router), `stages.json` (single-source stage language),
`demo-run.json` + `demo-run.cfpb.json` (replay data), `review-queue.json`, `version-timeline.json`,
`pages/manifest.json`. **Subdirs:** `pages/` (4 view JS + manifest), `stages/` (6), `pipeline/` (8 + css),
`styles/` (4 css), `components/` (empty), `assets/` (empty), `recorders/` (empty).

### 1C. Admin/demo server — every page route (`scripts/baltor_admin_demo_server.py`)

| Route | Serves | Purpose | Type |
|-------|--------|---------|------|
| `/`, `/admin-demo` | `home_page()` | Six-tile admin demo home | page |
| `/admin-demo/sources` | `sources_page()` | Load/upload/connect data | page |
| `/admin-demo/run-sample` | `create_background_run()` | Load built-in CFPB sample → monitoring | action |
| `/admin-demo/monitoring` | `monitoring_page()` | Processing status of current run | page |
| `/admin-demo/outputs` | `outputs_page()` | Outputs & artifacts of current run | page |
| `/admin-demo/download` | `download_page()` | Export/download run (zip/JSON) | page |
| `/admin-demo/explore` | `explore_page()` | RAG records / context inspection | page |
| `/admin-demo/testing` | `testing_page()` | Integration testing + readiness checklist | page |
| `/admin-dashboard`, `/admin-dashboard/monitor` | `monitor_page()` | Queue health, events, heartbeats | page |
| `/dashboard`, `/dashboard.html` | static `dashboard.html` | Live Ops Dashboard | page |
| `/dev`, `/dev-dashboard.html` | static `dev-dashboard.html` | Dev flywheel | page |
| `/hub`, `/hub.html` | `hub.html` | Control hub | page |
| `/raw`, `/raw.html`, `/feed` | `raw.html` | Raw feed | page |
| `/integrate`, `/integrate.html`, `/cfpb` | `integrate.html` | CFPB integration demo | page |
| `/consume`, `/consume.html` | `consume.html` | Consumption showcase | page |
| `/memory`, `/memory.html` | `memory.html` | Memory page | page |
| `/standards`, `/standards.html` | `standards.html` | Standards registry | page |
| `/determinism`, `/determinism.html` | `determinism.html` | Determinism factory | page |
| `/temporal-graph`, `/temporal-graph.html` | `temporal-graph.html` | Temporal fact graph | page |
| `/native`, `/native.html` | `native.html` | Native format preservation | page |
| `/inference-plane`, `/inference-plane.html`, `/inference` | `inference-plane.html` | Shared LLM Plane | page |
| `/fleet`, `/fleet.html` | `fleet.html` | Fleet/supervisor | page |
| `/pipeline`, `/pipeline.html`, `/pipeline/index{,.html}` | `_serve_pipeline_file("index.html")` | Pipeline journey index | page |
| `/pipeline/<file>` | `_serve_pipeline_file(rel)` | Pipeline static files (pages/*.html, pipeline.css) | page |
| `/cfpb-artifact-graph{,.html}` | `cfpb-artifact-graph.html` | CFPB artifact graph | page |

### 1D. Admin/demo server — every API route (all 80)

**`/api/context/*` + `/api/runtime/*` → `api_context_handler` (projection; serve is state-changing):**
`POST/GET /api/context/serve` · `GET /api/context/responses/<id>` · `GET /api/context/receipts/<id>` ·
`GET /api/runtime/sections` · `GET /api/runtime/consumption`.

**`/api/memory/*` → `api_memory_handler` (projection):** `GET /api/memory/artifacts` · `/profile` · `/search` ·
`/connectors` · `/providers` · `/traces`.

**`/api/pipeline/*` → `api_pipeline_handler` (projection):** `GET /api/pipeline/overview` · `/upload` ·
`/decomposition` · `/reconciliation` · `/enhancement` · `/optimization` · `/verification` · `/consumption`.

**`/api/native/*` → `api_native_handler`:** `POST /api/native/ingest` (stores source bytes+sha256) ·
`GET /api/native/export/<id>?mode=` · `/sidecar/<id>` · `/diff/<id>` · `/annotations/<id>` (all projection).

**`/api/standards/*` → `api_standards_handler` (projection):** `GET /api/standards/patterns` · `/templates` ·
`/routines` · `/waivers` · `/maturity` · `POST/GET /api/standards/generate-preview` (dry-run, writes nothing).

**`/api/determinism/*` → `api_determinism_handler` (projection):** `GET /api/determinism/overview` · `/traces` ·
`/consensus` · `/patterns` · `/rules` · `/replay` · `/shadow` · `/promotions` · `/fallback`.

**`/api/graph/temporal/*` → `api_temporal_graph_handler` (projection; rebuild projection-only):**
`GET /api/graph/temporal/facts` · `/edges` · `/conflicts` · `/held-out` · `/provider-status` ·
`/timeline/<fact_key>` · `/current/<fact_key>` · `/current` · `/query` · `POST /api/graph/temporal/rebuild`.

**`/api/inference/*` → `api_inference_handler` (projection; structured-local = candidate):**
`GET /api/inference/providers` · `/model-graph` · `/free-endpoints` · `/preferences` · `/health` · `/receipts` ·
`POST /api/inference/resolve-preference` · `POST /api/inference/structured-local`.

**`/api/context-gateway/*` (inline, projection):** `GET /status` · `/connectors` · `/sync-contracts` ·
`/context-object-schema` · `/context-schema-catalog` · `/product-surface` · `GET/POST /search` · `/fetch` ·
`/glossary` · `/dimensions` · `/model-routing` · `/reranking` · `/local-memory` · `GET /trace?result_id=`.

**`/api/admin-dashboard/*` (inline, projection):** `GET /events` · `/status` · `/queue-health` ·
`/operational-readiness` · `/heartbeat?run_id=`.

**`/api/fleet*` → `supervisor_projection` (projection):** `GET /api/fleet` · `/api/fleet/<section>` ·
`/api/fleet/supervisors/<id>`.

**`/api/demo/*` + `/api/admin-demo/*` (inline, state-changing):** `POST /api/demo/run-full-pipeline` ·
`POST /api/demo/run-full-pipeline-via-fleet` · `POST /api/demo/integrate-cfpb` · `POST /api/demo/cfpb-artifact-graph` ·
`POST /api/admin-demo/runs` · `GET /api/admin-demo/runs/<id>` · `GET /api/admin-demo/runs/<id>/exports/<kind>`.

**`/api/dev/*` (inline, state-changing + projection):** `GET /api/dev/status` · `/pipelines` · `/pipelines/runs` ·
`/pipelines/runs/<id>` · `/pipelines/runs/<id>/lineage` · `POST /api/dev/enqueue` · `/pipelines/run` ·
`/tenant-ingest` · `/drain`.

**`/api/events*` (inline):** `GET /api/events` · `GET /api/events/stream` (SSE) · `POST /api/events/clear`.

**Health (inline, projection):** `GET /api/health` · `GET /api/debug/heartbeat?run_id=`.

---

## 2. CONTEXTISEVERYTHING (holding company)

| Page | Location | Purpose | Status |
|------|----------|---------|--------|
| Parent mission landing | `web/context-is-everything/index.html` | Front door above Baltor + OHH; locked brand messaging | BUILT |
| GTM launch guide | `web/context-is-everything/gtm-launch-guide.html` | Go-to-market guide | BUILT |
| Portfolio one-pager | `dist/sites/contextiseverything/index.html` | Anchors: hero · what-it-is/owns · what-it-is-not · who-for · thesis · companies · how-it-fits | BUILT |

---

## 3. TELEON

| Surface | Location | Pages | Status |
|---------|----------|-------|--------|
| Teleon.dev one-pager | `websites/teleon.dev/` → `dist/sites/teleon.dev/index.html` | hero · owns · not · who-for · core design · runtime adapters · dashboards · how-it-fits | BUILT |
| **Teleon Control Tower (staff)** | — | — | **NONE (greenfield)** |
| **Capability Assurance Portal (customer)** | — | — | **NONE (greenfield)** |

---

## 4. OPENHARNESSHUB

**4A. One-pager:** `websites/openharnesshub/` → `dist/sites/openharnesshub/index.html` (hero · owns · not · who-for ·
governance rule · contains · preferred site · how-it-fits). **BUILT.**

**4B. Product app `web/harness-hub/` — every route:**

| Route | View | Purpose | Status |
|-------|------|---------|--------|
| `/` | PLanding | Landing with modality tabs (Text·Image·Audio·Video) + example chips + A/B hero | LIVE |
| `#/preview` | PPreview | Logged-out build funnel; calls real `/api/build` | LIVE |
| `/pipelines` | catalog.js | Browse pipelines | TEMPLATE |
| `/components` | catalog.js | Browse components | TEMPLATE |
| `/c/:slug` | catalog.js | Component detail | TEMPLATE |
| `/build` | build.js | Build a pipeline | TEMPLATE |
| `/results` | run.js | Build/run results | TEMPLATE |
| `/flow` | flow.js | Flow/DAG editor | TEMPLATE |
| `/run` | run.js | Run a pipeline | TEMPLATE |
| `/workers` | admin.js | Worker foundry | TEMPLATE |
| `/byo` | byo.js | Bring-your-own component | TEMPLATE |
| `/freshness` | govern.js | Freshness/CDC view | TEMPLATE |
| `/attest` | govern.js | Attestation | TEMPLATE |
| `/trust` | govern.js | Trust view | TEMPLATE |
| `/audit-log` | govern.js | Audit log | TEMPLATE |
| `/improve` | requests.js | Improvement requests | TEMPLATE |
| `/connect` | requests.js | Connect sources | TEMPLATE |
| `/sources` | requests.js | Source management | TEMPLATE |
| `/admin` | admin.js | Admin | TEMPLATE |
| `/checkout` | admin.js | Checkout/billing | TEMPLATE |
| `/solutions` | sdg.js | SDG solutions | TEMPLATE |
| `/value` | value.js | Value page | TEMPLATE |
| `/why` | why.js | Why page | TEMPLATE |
| `/docs` | docs.js | Docs | TEMPLATE |
| `/compare` | compare.js | Compare | TEMPLATE |
| `/deep` | deep.js | Deep research | TEMPLATE |

(Served by `scripts/showcase/server.py`; design = oh-tokens/oh-components/oh-explorations, dir-s ember accent.)

**4C. Catalog (`catalog/` — data, not pages):** adapters(17) · benchmarks(111) · datasets(205) · harnesses(195) ·
knowledge-packs(327) · logic-packs · patterns(50) · personas(233) · pipelines(281 domains) · processors(27) ·
rubrics(245) · rule-packs(6) · tools(157). The public openharnesshub.com catalog pages render from this.

---

## 5–7. OPENCONTEXTHUB · OPENSKILLSHUB · OPENTOOLSHUB

Each is a single one-pager (`websites/<hub>/content.md` → `dist/sites/<hub>/index.html`) with the standard anchors:

| Site | Distinct anchors | Status |
|------|------------------|--------|
| OpenContextHub | core rule · artifact types · visibility · how-it-fits | BUILT |
| OpenSkillsHub | governance rule · SKILL.md packages · feeds the portfolio · how-it-fits | BUILT |
| OpenToolsHub | governance rule · tool kinds · feeds the portfolio · how-it-fits | BUILT |

(All also share: hero · what-it-is/owns · what-it-is-not · who-for.) No interactive registry/browse UI yet — positioning pages only.

---

## 8–10. OPENMCPHUB · OPENCOMPRESSIONHUB · OPENBENCHMARKHUB — **GAP**

| Hub | Backing data | Site | Status |
|-----|--------------|------|--------|
| OpenMCPHub | — | — | **NONE** (not in `portfolio_lib.SITES`) |
| OpenCompressionHub | Context Efficiency Spine concept | — | **NONE** |
| OpenBenchmarkHub | `catalog/benchmarks/` + `architecture/open_benchmark_registry.json` + `schemas/benchmarks/*` | — | **NONE (no site)** |

---

## 11–12. DEMO CONTROL TOWER & PORTFOLIO HUB

| Surface | Location | Pages | Status |
|---------|----------|-------|--------|
| Demo Control Tower | `dist/sites/demo-control-tower/index.html` | Single meta-index: start-here · portfolio sites · product demos · dashboards · open-hub registries · internal tools · demo script · caveats; local + TryCloudflare URLs + honest status | BUILT |
| Portfolio hub | `dist/sites/portfolio/index.html` | Single nav page linking 7 brand sites + the tower | BUILT |

---

## 13. PRIMITIVES

### 13A. UI / design-system primitives (every class — `web/baltor/styles/`)

| Primitive | File | Purpose |
|-----------|------|---------|
| Design tokens | `oh-tokens.css` | colors/radius/shadow/font/scale for 9 directions × light/dark; only `--accent` differs per brand |
| Button | `oh-components.css` | `.oh-btn` (`--primary`/`--ghost`/`--sm`) |
| Card / surface | `oh-components.css` | `.oh-card` (+`--pad`/`--interactive`); `.pt-panel` alias |
| Badge / chip | `oh-components.css` | `.oh-badge` (lift/verified/warn/danger/muted/stable) |
| Headings / eyebrow / section label | `oh-components.css` | `.oh-h1` `.oh-h2` `.oh-eyebrow` `.oh-section-label` |
| Tabs | `oh-components.css` | `.oh-tabs` `.oh-tab` (underline indicator) |
| Segmented control | `oh-components.css` | `.oh-segment` `.oh-seg` |
| Form field / input | `oh-components.css` | `.oh-field` `.oh-input` |
| Switch / toggle | `oh-components.css` | `.oh-switch` (animated knob) |
| Table / settings row | `oh-components.css` | `.oh-table` `.oh-setrow` |
| Meter / progress | `oh-components.css` | `.oh-meter` `.oh-prog` (is-done/is-indet) |
| Code block | `oh-components.css` | `.oh-code` |
| Banner / alert | `oh-components.css` | `.oh-banner` (accent-left border) |
| Stat / metric tile | `oh-components.css` | `.oh-stat` (`.v`/`.k`) |
| Nav / wordmark / mark | `oh-components.css` | `.oh-nav` `.oh-wordmark` `.oh-mark` |
| Topbar / appbar | `oh-components.css`+`proto.css` | `.oh-topbar` `.oh-appbar` `.pt-topbar` |
| Sidebar / nav item | `proto.css` | `.pt-side` `.pt-navsec` `.pt-navitem` `.pt-side-foot` |
| Page layout / shell / split | `oh-components.css`+`proto.css` | `.oh-shell` `.oh-page` (+`--wide`) `.oh-split` `.pt-shell` |
| Marketing shell / hero | `oh-components.css` | `.oh-mkt` `.oh-hero` `.oh-hero-title` |
| Entry box / CTA / chips | `oh-components.css` | `.oh-entrybox` `.oh-entry-row` `.oh-constraint-add` `.oh-chips` |
| Command palette | `proto.css` | `.pt-cmdk` `.pt-cmdk-modal` |
| Drawer / inspector | `proto.css` | `.pt-drawer` (slide-in) |
| Component card | `oh-components.css` | `.oh-comp-card` `.oh-cc-top` `.oh-cc-name` `.oh-cc-badges` |
| Flow canvas / DAG / node / operator | `oh-components.css`+`oh-explorations.css` | `.oh-flow` `.oh-fnode` `.oh-fop` `.oh-flow-svg` |
| Legend bar | `oh-components.css` | `.oh-legend-bar` `.oh-legend-chip` |
| Vertical flow diagram | `oh-explorations.css` | `.oh-vstage` `.oh-vnode` `.oh-vconn` `.oh-vop` |
| Subway / linear diagram | `oh-explorations.css` | `.oh-sub-stage` `.oh-sub-line` `.oh-sub-stop` `.oh-sub-bullet` `.oh-sub-rail` |
| Trace / audit log | `oh-explorations.css` | `.oh-trace-stage` `.oh-trace-hd` `.oh-trace-row` `.oh-trace-list` (+ `.k-*` kind colors) |
| Batch / loop wrapper | `oh-explorations.css` | `.oh-batch-stage` `.oh-batch-wrap` `.oh-batch-inner` |
| Palette card | `oh-explorations.css` | `.oh-pal` `.oh-pal-ramp` `.oh-pal-accents` `.oh-pal-prims` |
| Comparison table / rubric | `oh-explorations.css` | `.oh-cmp-table` `.oh-cmp-body` `.oh-rubric` |
| Result / recommendation card | `oh-components.css`+`oh-explorations.css` | `.oh-result` (+`--rec`) `.oh-result-lift` `.oh-result-cost` `.oh-rf-hero` `.oh-rf-flow` |
| Budget / quality dial | `oh-explorations.css` | `.oh-dial-stage` `.oh-slider` `.oh-curve` `.oh-dial-readout` |
| Capability-lift evidence | `oh-explorations.css` | `.oh-lift-panel` `.oh-lb-track` `.oh-lb-fill` `.oh-lift-delta` |
| Component library cols | `oh-explorations.css` | `.oh-lib-stage` `.oh-lib-col` `.oh-lib-chip` `.oh-lib-colname` |
| Scheme switcher | `oh-explorations.css` | `.oh-sw` `.oh-sw-trigger` `.oh-sw-panel` `.oh-sw-grid` `.oh-sw-row` |
| State messaging | `oh-explorations.css` | `.oh-state-msg` `.oh-state-empty` `.oh-state-toast` `.oh-skel-line` |
| Pricing tiers | `proto.css` | `.pt-tiers` `.pt-tier` (`.open`/`.feat`) `.pt-openline` |
| Account / settings / facets | `oh-components.css`+`proto.css` | `.pt-acct` `.pt-setrow` `.pt-facet` `.pt-facet-opt` |
| Responsive grids | `proto.css`+`oh-components.css` | `.pt-grid-3` `.pt-cards-grid` |
| Density / intensity tweaks | `proto.css` | `.tw-text-*` `.tw-int-*` `.tw-dens-*` |
| Keyboard hint / status dot | `oh-components.css` | `.oh-kbd` `.oh-execdot` |
| `proto.css` | `proto.css` | App-shell prototype primitives (sidebar/topbar/cmdk/drawer/tiers) |

**Rules:** Hanken Grotesk + IBM Plex Mono = dir-d (Baltor); only `--accent` differs per brand (Baltor teal
`#0e7c86`/`#2dd4bf`, coupled to `--verified`); all color/space/radius from CSS vars (never raw hex); focus =
`2px solid var(--accent)`. 9 directions (a editorial · b clinical · c product-dark · d Baltor · e blueprint ·
f ledger · g hacker · h enterprise · s OHH-ember) × light/dark.

### 13B. The seven product primitives (`docs/concepts/component-taxonomy-and-stages.md`)

| # | Primitive | Product name | Schema type(s) |
|---|-----------|--------------|----------------|
| 1 | Input | Input | `inputs` |
| 2 | Knowledge Corpus | **Knowledge Corpus** | `knowledge-pack`, `dataset` |
| 3 | If Statement | **If Statement** | `rule-pack`, `logic-pack` |
| 4 | Action | **Action** | `persona`, `tool`, `processor`, `harness`, `adapter`, `rubric`, `benchmark` |
| 5 | Loop | Loop | `pattern`, `pipeline` |
| 6 | Stop / End | Stop/End | (structural) |
| 7 | Output | Output | (structural) |

Primitive-legend colors (in tokens): `--p-input` grey · `--p-knowledge` green · `--p-conditional` gold ·
`--p-action` red · `--p-loop` purple · `--p-stop` red · `--p-output` blue · `--operator` gold.

---

## 14. Consolidated gaps & work needed (prioritized)

### P1 — Missing surfaces (named in strategy, no UI)
1. **Teleon Control Tower (staff) + Capability Assurance Portal (customer)** — entirely greenfield. The flagship runtime
   SaaS has **no UI**. Largest gap. (Greenfield TS per `prompts/teleon-build-kit.md`.)
2. **OpenMCPHub / OpenCompressionHub / OpenBenchmarkHub** — named hubs, **no one-pager, not in `portfolio_lib.SITES`**.
   OpenBenchmarkHub has data/contracts; the other two need at least positioning pages.

### P2 — Half-built product apps
3. **OpenHarnessHub app** — landing + `#/preview` live; **~24 routes TEMPLATE** (explore/build/flow/run/govern/connect/
   admin/docs/compare/deep/value/why/solutions) — CSS+tokens ready, JS route handlers pending.
4. **Baltor portfolio one-pager — RESOLVED (2026-06-07):** `dist/sites/baltor/index.html` **does exist** (it is in
   `portfolio_lib.SITES`/`SITE_ORDER`/`PORTS`); the earlier "missing" note was a scoped-`ls` false alarm. Baltor has
   both a portfolio one-pager and the `web/baltor/` SPA. No action needed.

### P3 — Design-system migration debt
5. **`dashboard.html` + `native.html` use ad-hoc inline dark-theme CSS** (raw hex, own `--bg/--panel/--line`) instead of
   the `oh-*` tokens — violates the branded-house "no hardcoded hex in a site stylesheet" rule. Migrate to
   `.oh.dir-d.theme-dark` (or formalize a dir-d-ops variant).
6. **`.pt-` vs `.oh-` duplicate classes** across `oh-components.css` + `proto.css` — converge on `.oh-`.
7. **Unused directions** (dir-a/b/c/e/f/g/h defined, no site consumes them) — archive or build a design-system showcase.
8. **`--p-*` primitive colors not auto-wired** — `.oh-fnode` needs manual `--nodehue`; add a data-primitive → color map.
9. **No `COMPONENTS.md`** in `docs/design/openharness-claude-design/` — token scopes documented, per-component
   states/nesting not.
10. **No shared responsive breakpoint tokens** — components hardcode `@media` widths (1024/1000/820/640px).

### P4 — API/route coverage gaps (admin server)
11. **No unified `/api/receipts/*` audit API** — receipts are scattered across context/pipeline/native/standards/
    inference handlers. A single audit-trail endpoint would feed the Demo Control Tower + any portal.
12. **No first-class `/api/source/*`, `/api/tasks/*`, `/api/worker/*`** — sources/tasks/workers visible only indirectly
    (runs, `/api/fleet`, heartbeat). Fine for the demo; needed before a real Control Tower.
13. **GET/POST auth asymmetry** — POST routes are token-gated, GET projections are not; several gateway routes accept
    both verbs. Pick one convention before any non-demo exposure.
14. **Inference has no dedicated stage-board tile** on the dashboard (it fires under the Enhancement macro-stage; it is
    on the header link + event stream). Optional polish.

### P5 — Hygiene / structure
15. **Empty reserved dirs** in `web/baltor/`: `components/`, `assets/`, `recorders/` — use or remove.
16. **`stages/` vs `pipeline/` overlap** (reconciliation/enhancement/optimization/consumption in both) — document the
    intended distinction (macro-stage explainer vs single-run walk) so it doesn't read as duplication.
17. **Public tunnel instances run old source** — the 5 long-running admin instances predate the inference-plane wiring;
    a same-port exact-pid restart surfaces it on the live demo (owner-gated, outward-facing).

---

## 15. Appendix — counts

- **Baltor:** 4 SPA views · ~35 static HTML (incl. `stages/`×6, `pipeline/`×8) · 4 CSS primitive files ·
  ~33 admin page routes · **80 API routes** across 8 dedicated handler modules + inline families.
- **Portfolio/hub one-pagers built (8):** contextiseverything, teleon.dev, openharnesshub, opencontexthub,
  openskillshub, opentoolshub, portfolio, demo-control-tower.
- **OpenHarnessHub app:** 2 live routes + ~24 templated routes.
- **Hubs named vs sited:** 7 named; **4 sited** (OHH, OpenContext, OpenSkills, OpenTools); **3 none** (OpenMCP,
  OpenCompression, OpenBenchmark).
- **UI primitives:** ~45 class families across tokens/components/explorations/proto; **9** directions × 2 themes.
- **Product primitives:** 7 (Input · Knowledge Corpus · If Statement · Action · Loop · Stop/End · Output).
- **Surfaces with NO UI:** Teleon Control Tower, Capability Assurance Portal, OpenMCPHub, OpenCompressionHub,
  OpenBenchmarkHub (5).
