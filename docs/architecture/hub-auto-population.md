# Auto-populating the Open*Hubs — custom tools + Teleon-managed capabilities

How each Open*Hub continuously gets stronger, automatically. Two layers, one descent, one self-reinforcing flywheel.

## 1. Two layers
- **Custom tools (the HOW)** — a tiered TOOL REPOSITORY, unbounded→bounded: `api` (GitHub, HN search) → `search`
  (HN Algolia) → `scrape` (chromium JS render). Stateless OpenClaw plugins call them; OpenClaw always picks the
  **most bounded available** tool that can serve (the descent). Real today: `research_radar` GitHub, HN Algolia,
  chromium JS scrape (`e2e/scrape_url.mjs`). More register here (web-search providers, arxiv, package registries).
- **Teleon-managed capabilities (the WHAT)** — each hub gets a plain-text capability *"continuously update this hub
  with public repos / skills / context / …"*. Teleon **descends** it (`src/teleon/hub_freshness.py::keep_hub_fresh`):
  UNBOUNDED broad discovery across the whole tool repo → digest into the hub → **descend to the cheapest bounded tool**
  that still meets the freshness bar → record the move in the one descent brain. Future runs are cheap.

The *what each hub pulls from* is single-sourced in `architecture/hub_population_strategy.json` (per hub: content kind,
sources — GitHub topics / HN queries / seed URLs — tool tier, freshness + verify bars).

## 2. The pipeline (per hub, per cycle)
`scrape/search/api (OpenClaw plugins) → ingest → digest → rank → verify → version → serve`
(`src/openharnesshub/hub_engine.py` + `component_store.py`). Governed at every step: discovered items are CANDIDATES
(`serves_truth=false`), content-hash deduped, losslessly versioned, and **served only after the verify+rank gate**
(discovery ≠ trust). Users keep their own tenant-isolated versions; opt-in `contribute` promotes to global.

## 3. The recursive flywheel (why the hubs compound)
The tools/skills/harnesses that *do* the population are themselves hub components — so populating a hub improves the
machinery that populates it:
- **OpenToolsHub** → better tools for OpenClaw → discovers more/better components.
- **OpenSkillsHub** → better digest/plan skills for Teleon → better breakdown of the capability.
- **OpenHarnessHub** → better eval harnesses for the verify/rank gate → better ratings, higher-quality served set.
- **OpenCompressionHub** → cheaper context for every step.

So each hub gets stronger *and* makes every other hub's population stronger. The descent brain learns the cheapest
discovery path per hub, so it gets cheaper as it gets better.

## 4. Scheduling (continuous, 24/7)
The `hubs` flywheel in `scripts/flywheel_orchestrator.py` runs the freshness capability for **one hub per cycle**
(round-robin), using the real tool repository + the strategy. Resilient (a source failure is skipped, never fatal),
cheap (the descent), governed. Halts only on `.agent/STOP_REQUESTED`. On-demand: `scripts/hub_engine_runner.py
--fresh "<intent>"` / `--discover "<q>"`.

## 5. Governance (non-negotiable)
Candidates `serves_truth=false`; served only after verify+rank; content-hash dedupe; lossless versioning;
tenant-private never global without opt-in contribute; official APIs / robots-respecting scraping; the aggregate funnel
(lead-gen + the substrate feed to Teleon/Baltor) is PII-free and never leaks raw tenant rows.

Proofs: `check_openclaw_hermes`, `check_hub_freshness`, `check_hub_engines`. Design source-of-truth for sources:
`architecture/hub_population_strategy.json`.
