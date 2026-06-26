# Panel round 1 — kimi-k2.7-code (kimi-k2.7-code)

> CANDIDATE · serves_truth=false · CEO/COO/CTO/CFO/YC lenses

## CEO Lens

**2 biggest strengths**
- The strategic positioning is sharp and well-articulated: “AI Done Right” frames Baltor as the applied context product, Teleon as the eval-gated runtime that descends LLM spend toward deterministic/bounded implementations, and OpenHarnessHub as the open spec/ecosystem. The dependency law (`architecture/portfolio_dependency_law.json`, enforced by `scripts/check_portfolio_dependency_law.py`) shows a coherent layered ambition.
- The market thesis is large and timely: enterprises are desperate to cut LLM cost, increase determinism, and satisfy compliance. The CapabilityTask spec / OpenHarnessHub play (`docs/strategy/teleon-baltor-openharnesshub-portfolio.md`) could become a platform standard if it gains adoption.

**2 most serious risks**
- Focus vs. sprawl is catastrophic. The portfolio snapshot in `CLAUDE.md` lists **Baltor + Teleon + 22 Open\*Hubs** (9 live open registries + 13 private-bench registries), backed by 1,430 Python modules, 124 `architecture/*.json` registries, and 470 `scripts/check_*.py` proof gates. A buyer or investor hears “we built everything” instead of “we solve one urgent thing.”
- There is no evidence of paid traction. The entire descent value proposition is demonstrated against internal fixtures (`architecture/modality_capability_catalog.json`) with estimated constants, not against a paying customer’s workload.

**1 concrete recommendation**
- Consolidate to **one monetizable SKU and one lighthouse vertical**. Park the 13 private-bench hubs and most of the 9 open registries; run Baltor as the **first paying tenant of Teleon**, not as a parallel product. Set a 90-day revenue milestone before expanding the ecosystem. (`CLAUDE.md`, `docs/strategy/teleon-baltor-openharnesshub-portfolio.md`, `scripts/check_ai_done_right_surface_family.py`)

---

## COO Lens

**2 biggest strengths**
- The engineering culture is invariant-driven and auditable: dependency-law checks, storage-tier policy (`architecture/storage_tier_policy.json`), content-addressed idempotency, and the capability PR/CI gate (`src/teleon/storage/capability_pr.py`) form the skeleton of a scalable operating model.
- The backend-swappable record-store design (`src/teleon/storage/record_store.py`) correctly separates the storage port from the caller, with a clear local/cloud tier policy.

**2 most serious risks**
- Almost nothing is actually shipping to production. `PostgresRecordStore` and `WarehouseRecordStore` in `src/teleon/storage/record_store.py` literally `raise NotImplementedError`; the cloud scale path is a design document, not working infrastructure. The 470 check scripts mostly verify scaffolding invariants, not product behavior.
- The biggest throughput bottleneck is the **missing closed loop between runtime telemetry and the descent brain**. `src/teleon/evolution/catalog_descent.py` writes synthetic `DescentAttempt`s from fixture flags (`deterministic_achievable`), while real `RunObservation`s (`src/teleon/objectives/telemetry.py`) and `ModelInvocationReceipt`s (`src/teleon/inference/receipts.py`) are not feeding `src/teleon/evolution/descent_attempt_store.py`.

**1 concrete recommendation**
- Close the telemetry-to-brain loop: **every receipt and run observation must generate a `DescentAttempt`**. Freeze new registry creation until this loop is live, and ship one merged “capability PR” per week on a real workload using `src/teleon/storage/capability_pr.py`. (`src/teleon/inference/receipts.py`, `src/teleon/objectives/telemetry.py`, `src/teleon/evolution/descent_attempt_store.py`)

---

## CTO Lens

**2 biggest strengths**
- The port/adapter architecture is sound: dependency law, OIPS preference engine (`src/teleon/inference/oips.py`), inference adapters (`src/teleon/inference/adapters.py`), git backend port (`src/teleon/storage/git_backend_port.py`), and record-store port are cleanly separated.
- The append-only, content-addressed storage design with SQLite-WAL + durable JSONL mirror (`scripts/_jsonl_store.py`) is a reasonable offline substrate.

**2 most serious risks**
- Build-vs-buy is wrong in high-leverage places. The team is building custom adapters for every provider endpoint, a custom freshness/CDC runtime, a custom git backend, and unimplemented Postgres/Warehouse stores. These should largely be bought: a gateway library for model routing, managed Postgres/BigQuery for storage, and managed GitHub/GitLab for VCS.
- The system will break first under load at the descent brain. `DescentAttemptStore.training_examples()` and `stats()` call `self.all()` and scan every record in Python; `_rewrite_mirror_locked` in `scripts/_jsonl_store.py` rewrites the entire JSONL mirror from DB rows; and SQLite single-writer serialization will collapse under concurrent append traffic. The “billions-to-trillions of rows” claim is not supported by the current implementation.

**1 concrete recommendation**
- (a) Implement or buy the scale backends: make `PostgresRecordStore` and `WarehouseRecordStore` real and partition the brain by tenant/task. (b) Replace the full-scan meta-learner with incremental online aggregates. Stop adding custom inference adapters and adopt a production gateway. (`src/teleon/storage/record_store.py`, `src/teleon/evolution/descent_attempt_store.py`, `scripts/_jsonl_store.py`, `src/teleon/inference/adapters.py`)

---

## CFO Lens

**2 biggest strengths**
- The value proposition is margin-friendly if real: reducing LLM usage and increasing determinism creates a clear savings pool to price against. `src/teleon/evolution/substrate_selector.py` uses real model-index cost ratios, not guessed constants.
- Unit-level cost instrumentation exists: `RunLedger` (`src/teleon/objectives/telemetry.py`), `ModelInvocationReceipt` (`src/teleon/inference/receipts.py`), and `model_efficiency.py` provide the raw material for cost accounting.

**2 most serious risks**
- The cost-descent thesis is currently fiction. `src/teleon/evolution/catalog_descent.py` uses hard-coded `_MODEL_STAGE_COST = 0.05` and `_DET_STAGE_COST = 0.002` estimates plus `deterministic_achievable` flags from the catalog, not measured customer spend. No pricing or revenue model is visible anywhere in the pack.
- Burn is likely enormous relative to output: 1,430 modules, 124 registries, 470 scripts, and 22 hubs consume engineering runway before any proven revenue. The runway is being spent on scaffolding, not product.

**1 concrete recommendation**
- Replace the estimated stage costs in `catalog_descent.py` with actual per-run costs from `RunLedger`/`receipts`, then price Teleon as a share of measured savings or a per-capability subscription, and publish a margin model. (`src/teleon/evolution/catalog_descent.py`, `src/teleon/objectives/telemetry.py`, `src/teleon/inference/receipts.py`, `src/teleon/inference/model_efficiency.py`)

---

## YC Lens

**2 biggest strengths**
- Why-now is real: LLM cost, non-determinism, hallucination, and compliance pain are acute. The “descend to deterministic” framing is a credible wedge.
- Default-alive potential exists if the team can stay local-first: the Ollama lane, free endpoint intelligence, and low cloud infra footprint could keep burn low.

**2 most serious risks**
- This is a research project, not a startup. Building 1,430 modules and 470 proof gates before a single paid customer is classic over-engineering. The 22-hub portfolio (`CLAUDE.md`) is a distraction from finding product-market fit.
- There is no validated “make something people want.” The demos (`catalog_descent.demonstrate`, `freshness_runtime.demonstrate_freshness_e2e`) are self-referential fixtures, not customer outcomes.

**1 concrete recommendation**
- Cut 80% of surface area. Pick one painful use case—e.g., regulated-fact freshness in `src/teleon/evolution/freshness_runtime.py`—and get **3 design partners to pay** before adding another hub or registry. (`CLAUDE.md`, `src/teleon/evolution/freshness_runtime.py`)

**Brutal question a YC partner asks:**  
“You have 1,430 modules and 470 check scripts—show me the one screen a customer pays for and the bank deposit that proves it.”

---

## TOP PRIORITY

**Ship one end-to-end paid Teleon capability on a real customer workload, with measured before/after cost and determinism, replacing the synthetic `src/teleon/evolution/catalog_descent.py` demo.** This single action unblocks revenue (CEO), forces the telemetry-to-brain loop to close (COO), exposes real load on storage and ends full-scan fantasy (CTO), produces actual margin data (CFO), and proves people want it instead of more hubs (YC). (`src/teleon/evolution/catalog_descent.py`, `src/teleon/inference/receipts.py`, `src/teleon/objectives/telemetry.py`, `src/teleon/storage/capability_pr.py`)