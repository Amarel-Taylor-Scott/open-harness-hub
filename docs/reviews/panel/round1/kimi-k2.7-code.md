# Panel round 1 — kimi-k2.7-code (kimi-k2.7-code)

> CANDIDATE · serves_truth=false · CEO/COO/CTO/CFO/YC lenses

## CEO Lens

**2 biggest strengths**
1. **The "descent" thesis is a real, defensible market position.** Moving AI capabilities down the cost/determinism/latency axes (e.g., document extraction 47–91% cheaper, enrichment 86% cheaper) addresses the dominant buyer pain in 2026: frontier-model bills and hallucination risk. The cascade in `src/teleon/extraction/document_extraction_cascade.py` and the search+LLM descent in `src/teleon/enrichment/search_enrich.py` are concrete instantiations of that story.
2. **Portfolio architecture is logically separated.** Baltor (governance/context), Teleon (runtime/descent), and OpenHarnessHub (neutral catalog) have a clean dependency law (`architecture/portfolio_dependency_law.json`) and a clear surface map (`architecture/surface_map.json`), which prevents the worst kind of monolith entanglement.

**2 most serious risks**
1. **Narrative collapse.** A buyer or investor hears "context engine + capability runtime + open hub + AI observer + 22 hubs + 5 surfaces + 1750 modules + 584 proof gates." There is no single, repeatable 30-second value proposition. The surface map alone lists `ai-done-right`, `baltor`, `teleon`, `openharnesshub`, `open-star-hubs`, `teleon-demos`, and `design-bundle` — too many brands before any one is a must-have.
2. **Existential sprawl.** The company is building a platform, a compiler, a context engine, an open ecosystem, an observer, a worker fleet, and 22 registries simultaneously. `docs/strategy/teleon-baltor-openharnesshub-portfolio.md` calls this "owner-decided," but there is no evidence in the code or docs that one vertical has been reduced to a paid, repeatable customer outcome.

**1 concrete recommendation**
Pick **one** live vertical — sanctions screening (`docs/strategy/first-live-capability-sanctions-screening.md`) or provider-directory freshness (`src/teleon/verticals/provider_directory.py`) — and make it a standalone, priced product that a customer can buy and run end-to-end. Freeze all new surfaces and hubs until that one vertical has 3 paying customers and measured unit economics. The current demo surfaces (`docs/status/teleon-demo.md`, `docs/status/openharnesshub-investor-demo.md`) are not substitutes for a paid wedge.

---

## COO Lens

**2 biggest strengths**
1. **Proof-gate discipline is real.** With 584 `scripts/check_*.py` proof gates, the team has built a quality bar that most early-stage platforms skip. That creates operational leverage if the gates are kept green and scoped.
2. **Ownership boundaries are explicit.** The dependency law (`architecture/portfolio_dependency_law.json`) and port/adapter structure (`src/teleon/ports/`, `src/baltor/ports/`) make it clear who owns what runtime concern, which is essential for a multi-product portfolio.

**2 most serious risks**
1. **Scaffolding epidemic.** Hundreds of modules are empty shells or stubs: `src/baltor/processors/*/__init__.py`, `src/baltor/llm_gateway/*/__init__.py`, `src/baltor/adapters/memory/supermemory_api.py` ("CONTRACT STUB"), and `src/baltor/adapters/memory/supermemory_mcp.py` ("CONTRACT STUB"). The `src/baltor/workers/execution_backend_selector.py` and most of `src/baltor/purpose_tasks/` are literally re-export shims from Teleon. This is scaffolding dressed as architecture.
2. **Registry maintenance drag.** 198 JSON registries in `architecture/` require manual curation. `src/openharnesshub/hub_engine.py` can run a flywheel, but there is no evidence of automated, high-volume population; the system is optimized for catalog completeness over customer throughput.

**1 concrete recommendation**
Declare a 90-day "surface freeze" and run a stub purge: delete or demote to `archive/` every module that contains only a docstring and an `__init__.py`, and consolidate the Teleon re-export shims in `src/baltor/` back to their canonical home in `src/teleon/`. Start with `src/baltor/processors/__init__.py`, `src/baltor/llm_gateway/__init__.py`, and `src/baltor/workers/execution_backend_selector.py`.

---

## CTO Lens

**2 biggest strengths**
1. **Clean dependency law and layered architecture.** Baltor depends on Teleon; Teleon consumes OpenHarnessHub; OpenHarnessHub depends on neither. This is enforced in `architecture/portfolio_dependency_law.json` and largely respected in the import graph, which is the right foundation for long-term maintainability.
2. **Deterministic core + lossless stores.** `src/baltor/determinism/trace_store.py` (append-only, content-addressed, tenant-scoped traces) and `src/baltor/distillation/lossless_store.py` (raw/source/derived layers with rollback) give the governance claims a real technical backbone.

**2 most serious risks**
1. **Shim-layer rot.** The dependency law is violated in spirit by widespread Baltor re-exports of Teleon modules: `src/baltor/workers/execution_backend_selector.py`, `src/baltor/workers/execution_dispatch.py`, `src/baltor/workers/execution_providers/*.py`, and `src/baltor/purpose_tasks/*.py` are all marked "RE-EXPORT SHIM (lossless extraction → Teleon)." This creates a maintenance hazard and confuses ownership.
2. **Scale facade.** Production backends are either stubs or unwired. `src/baltor/adapters/object_store/local_object_store.py` is an in-memory store that loses data on process restart. `src/teleon/storage/record_store.py` has `_UnwiredCloudStore` placeholders for Postgres and warehouse tiers. The fleet ledger (`src/teleon/workers/fleet_ledger.py`) and durable ledger (`src/teleon/workers/durable_fleet_ledger.py`) default to SQLite — fine for proofs, not for real multi-tenant load.

**1 concrete recommendation**
Stand up **one** staging environment where the operational tier is real Postgres + pgvector and the object store is S3-compatible, and delete the shim files by moving their canonical home to `src/teleon/`. Specifically: replace `src/baltor/adapters/object_store/local_object_store.py` with a persisted backend, and remove `src/baltor/workers/execution_backend_selector.py` after callers migrate to `src/teleon/runtime/execution_backend_selector.py`.

---

## CFO Lens

**2 biggest strengths**
1. **Cost-descent demos are measured, not assumed.** `src/teleon/extraction/document_extraction_cascade.py::extraction_savings` and `src/teleon/enrichment/search_enrich.py::enrichment_savings` compute baseline-vs-descended cost deltas, and the demo catalog claims 47–91% extraction savings and 86% enrichment savings. That is the kernel of a margin story.
2. **Multi-objective preference profiles.** `src/teleon/inference/preference_profile.py` lets a tenant weight cost, latency, determinism, and accuracy, which is the right primitive for differentiated pricing tiers.

**2 most serious risks**
1. **No pricing or billing plane.** There is no metered usage model, no customer contract schema, and no revenue recognition path in the code. `scripts/billing_ledger.py` and `scripts/billing_plane.py` exist as scripts but are not wired into the runtime path. The `architecture/execution_backend_pricebook.json` is a cost model, not a price list.
2. **Cost-to-serve explosion before revenue.** Maintaining 198 registries, 584 proof gates, 5 product surfaces, and 22 hubs for zero or few paying customers is high burn with no margin proof. The "descent saves money" thesis is a customer benefit, not a company margin — until there is a price and a cost-to-serve number.

**1 concrete recommendation**
Implement metered usage billing for **one** capability — e.g., document extraction per page, using `src/teleon/extraction/document_extraction_cascade.py` — and publish a price list in `architecture/execution_backend_pricebook.json`. Run a paid pilot with 3 customers and report actual cost-to-serve, gross margin, and payback period before building the next surface.

---

## YC Partner Lens

**2 biggest strengths**
1. **Why-now is real.** AI inference costs and hallucination liability are forcing teams to trade frontier models for cheaper, more deterministic paths. The timing is right, and the thesis is captured in `docs/strategy/context-layer-pmf.md` and `docs/strategy/inference-time-capability-watch.md`.
2. **Demo surfaces are wired and public.** `docs/status/openharnesshub-investor-demo.md` and `docs/status/teleon-demo.md` show live, verified URLs — the team can ship something visible.

**2 most serious risks**
1. **This is a research project, not a startup.** 5,138 docs, 198 registries, 37 strategy docs, and 38 codex operating guides before a single paid product is the opposite of "make something people want." The codebase looks like an architecture exercise funded to explore every adjacent possibility.
2. **No wedge.** "Context engine + capability runtime + open hub + observer" is four products. YC will ask: *What is the one thing you do better than anyone else for one specific customer?* The current answer is abstract.

**1 concrete recommendation**
Reduce the pitch to one sentence: *"We cut document-extraction AI costs 80% with the same accuracy."* Kill or freeze every surface, hub, and registry that does not directly serve that sentence for the next 6 months. The right starting point is `src/teleon/extraction/document_extraction_cascade.py` + `docs/use-cases/qa-on-documents.md`, not the full portfolio.

---

**TOP PRIORITY:** Pick **one** paid vertical (document extraction or sanctions screening), delete or freeze every surface/registry that does not serve it, replace the in-memory/SQLite scaffolding with real persisted backends for that vertical, and run a 3-customer paid pilot with metered billing and measured unit economics before writing another strategy doc or adding another hub.