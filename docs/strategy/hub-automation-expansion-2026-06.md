# Open*Hub automation — built now + the expansion space (2026-06-21)

How automated systems contribute content/tools/skills/modules/primitives to OpenHarnessHub + the 22 Open*Hubs, and
where this grows. Everything here is governed: discovered/generated items are **candidates** (`serves_truth=false`),
served only after the hub's verify gate (discovery ≠ trust); lossless versioning; tenant-private stays private until an
opt-in contribute. Coverage is enforced by `scripts/check_hub_population_coverage.py` (no hub silently lacks a path).

## The three contribution channels (every hub has ≥1; built)
1. **Discover** — `src/openharnesshub/discovery.py` (OpenClaw finder + Hermes router) + `src/teleon/hub_freshness.py`
   (`keep_hub_fresh`) search public sources, **unbounded→bounded** (cheapest tool that meets the freshness bar). A
   plugin is **auto-derived** per hub from `architecture/hub_population_strategy.json` — add a hub to the strategy and
   it gets a finder with no code edit.
2. **Generate** — `src/openharnesshub/generators.py` emits candidates from **our own systems** where no public source
   exists: `method_catalog` (reads `architecture/descent_method_catalog.json`, the single source — feeds the 5 method
   hubs + OpenTools modules), `descent_brain` (the descent_attempt_store — feeds OpenRouting; **operator-injected** so
   OHH never imports Teleon). Unwired generators return an honest `pending` marker, never fabricated candidates.
3. **Intake** — `scripts/hub_engine_runner.py --ingest` + `src/openharnesshub/intake.py`: the owner feeds **raw OKF /
   links / text** straight into a hub's lifecycle (digest → optional improve → verify → version). OKF parsing is
   lossless (raw kept). This is how login-walled sources (facebook/LinkedIn) get in — you paste the material; we don't
   scrape walled gardens.

## Research/browse as a descent-selectable catalog (built; the "hundreds of components" thesis)
Research itself is a **governed catalog** (`architecture/research_component_catalog.json`, 13 seed components across 6
tiers `feed<api<search<extract<render<browse`), selected by the same descent: an agent runner names the **detail it
needs** (a capability) + what it has (network/api_key/browser_runtime/llm) + a budget, and
`src/openharnesshub/research_catalog.select_component` returns the **cheapest eligible** component. The **low-cost-LLM-
driven Playwright browser** (`llm_driven_browser`, tier=browse) is a first-class component, selected **only** for
`deep_detail`/`js_render`/`interaction` that cheaper tiers can't get — and only when affordable + its runtime is
available. Guardrails (`architecture/research_guardrail_policy.json`) refuse login-walled hosts, cap per-host rate +
per-cycle cost, honor robots/ToS + official-APIs-first, and redact PII.

## The capability planner (built; open-ended → iterative/multi-component/scheduled)
`src/teleon/capability_planner.py` turns plain text ("scrape the internet for more skills for openskillshub.io") into
an executable plan: **classify** (iterative? scheduled? → cadence in cycles), **resolve hub** (domain or content-kind),
**infer the research capability** (drives the catalog descent), **decompose** into typed steps
(research_select → discover → digest → dedupe → [improve] → verify → version → [contribute]), and **execute** as a
**bounded loop** (stop on no-new-for-K-rounds / max_rounds) or emit a **schedule** the hubs flywheel honors. CLI:
`--capability "<text>" [--plan-only] [--rounds N]`.

## Standardized UI/UX (built)
`src/openharnesshub/hub_site.render_hub_page` — ONE branded template (Hanken Grotesk + IBM Plex Mono) renders all 22
surfaces with identical sections (hero+governance badge · 3 channels · browse · settings · substrate/funnel).
`scripts/build_hub_sites.py --all` writes them + an index; `scaffold_hub` uses the same template (a new hub looks like
the live 22 from day one).

---

## Expansion space (designed; prioritized next)

### More research/browse components (toward hundreds — the catalog is built to grow)
- **APIs/feeds:** Crates/RubyGems/Go proxy, Docker Hub, Papers-with-Code, OpenReview, Zenodo/DOI, Sourcegraph,
  ecosystem awesome-list parsers, Common Crawl index, Wikidata/DBpedia, sitemap-diff watchers (freshness).
- **Extract/render:** table extractor, schema.org/JSON-LD reader, OpenAPI/Swagger reader, repo-tree reader, notebook
  reader, transcript/caption extractor.
- **Browse drivers:** the `llm_driven_browser` real adapter (low-cost lane plans the **shortest** path to the target
  field, caps steps+tokens), a form-filling variant, an authenticated-with-owner-token variant (never stores creds).
- Each new component is itself **OpenToolsHub/OpenAgentHub content** (recursive flywheel: better tools → better
  population → stronger hubs).

### More integrations
- **Scheduling:** wire planner `schedule` descriptors to the flywheel per-hub cadence + an optional cron lane.
- **MCP-as-research:** an MCP server is both OpenMCPHub content **and** a research component (call its tools to enrich).
- **OKF round-trip:** export served components **as** OKF (we already ingest it) — the portable interchange both ways.
- **Generators to wire:** `compressor`, `eval_runs`, `review_board`, `template_instantiator`, `rl_env_synthesis`,
  `endpoint_probe`, `run_receipts/run_state` (each reads a real producer; injected like `descent_brain`).
- **Per-hub orchestrators:** the shared HubEngine already covers all 22; add per-hub ranker/verifier ports where a hub
  needs a specialized bar (e.g. OpenEndpointHub jurisdiction check, OpenSandboxHub conformance probe).

### More guardrails
- Per-capability **cost budget** on a planner run (not just per-cycle); backoff on rate-limit/429; fetch + honor
  live robots.txt; **PII scan** on ingested text (intake too); **provenance signing** of contributed components;
  **cross-hub dedupe** (a tool seen in OpenTools shouldn't re-enter via OpenAgent); tenant isolation assertions on
  intake; jurisdiction by **content**, not only host.

### More UI/UX screens (standardized)
- **Browse + search** within a hub (filter by kind/tier/verified); **contribute** forms for all 3 channels (paste OKF,
  add links, run a capability); the **settings plane UI** (already CLI-editable via `--set`); a **funnel/analytics**
  panel (the lead-gen view); a **per-hub dashboard** (cadence, last run, served growth) — all from the one template.

### More use cases (open-ended capabilities the planner already shapes)
- "keep OpenMCPHub current with new servers **weekly**" (scheduled) · "find agent harnesses and **improve** them for
  OpenHarnessHub" (improve step) · "collect **verified** endpoints and **share** the safe ones" (contribute step) ·
  "navigate each tool's docs for the **full** install detail" (deep_detail → browser) · "build a context pack for
  <domain> from these **links**" (intake).

## Status honesty
Built + self-tested: the 3 channels, research catalog + descent + guardrails, the planner, the standardized UI, the
coverage guard. Adapters marked `adapter`/`candidate` in the catalog (e.g. `llm_driven_browser`, `web_search`) need
their real runtime wired before live use. Generators beyond `method_catalog`/`descent_brain` are declared + `pending`.
