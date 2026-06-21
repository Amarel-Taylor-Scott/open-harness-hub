# External review — kimi-k2.7-code (via ollama)

> CANDIDATE · serves_truth=false · external model opinion (a proposal, never trusted truth).

## 1. ARCHITECTURE

### Strengths (real, but mostly on paper)

- **Clean dependency layering.** The enforced direction `Baltor → Teleon → OpenHarnessHub` and the explicit extraction of generic runtime code out of `src/baltor/` into `src/teleon/` is the right structural call. It keeps the runtime independently valuable and prevents the applied product from swallowing the platform. Cite: `docs/strategy/teleon-baltor-openharnesshub-portfolio.md`, `architecture/portfolio_dependency_law.json`, `scripts/check_portfolio_dependency_law.py`.
- **Append-only, content-addressed storage model.** The three-tier policy (`config` / `operational` / `history`) and the insistence that `serves_truth=false` for every stream is a coherent governance posture for evidence-based systems. Cite: `architecture/storage_tier_policy.json`, `src/teleon/storage/record_store.py`.
- **Freshness as a first-class axis.** Baking staleness (`STATUS_HELD_OUT_STALE`, volatility-matched cadence) into model selection is a genuinely useful idea for a world where model prices and endpoints rot constantly. Cite: `src/teleon/inference/model_index.py`, `src/teleon/evolution/descent_axes.py`.

### 3 most serious risks / weaknesses

1. **The central “DESCEND” loop is a skeleton, not a self-adaptive runtime.**  
   `src/teleon/evolution/descent_axes.py` defines 15 axes, but `src/teleon/evolution/descent_attempt_store.py` only tracks 5 of them (`cost`, `determinism`, `tokens_in`, `llm_usage`, `freshness`) and provides a dataclass with no learner, no policy, and no closed-loop writer. `src/teleon/evolution/substrate_selector.py` admits that until recently model-downgrade used a “guessed constant” and today only implements `model_downgrade()` for the cost axis, with a documented `_FALLBACK_DOWNGRADE_FACTOR = 0.1`. `src/teleon/objectives/objective.py` is a scoring utility, not an integrated selector. The product’s entire pitch is “DESCENDS non-deterministic capabilities,” but the runtime does not actually descend anything end-to-end.

2. **The storage scale claims are hand-waving.**  
   `architecture/storage_tier_policy.json` talks about “billions-to-trillions” rows and a warehouse backend, but `src/teleon/storage/record_store.py` implements the local backend as `sqlite_wal` plus JSONL mirrors. There is no demonstrated partitioning loader, no Parquet/ClickHouse/BigQuery implementation, no throughput numbers, and no proof that content-addressed idempotency is actually O(1) at scale. Asserting “the cloud backend is a config swap” is not the same as having built it.

3. **The portfolio is a scope explosion before a single product is proven.**  
   `CLAUDE.md` describes 1,427 Python modules, 124 architecture JSONs, 470 `check_*.py` scripts, 22 Open*Hubs, a private bench, a Baltor method spine, and a daily factory target of “1,000 to 5,000 database-backed component candidates.” `docs/strategy/teleon-baltor-openharnesshub-portfolio.md` admits the runtime extraction from Baltor is “incremental” with a `migration_status`. This is architecture astronautics: they are building a holding company, a naming stack, and a validation bureaucracy before demonstrating that one live tenant can run one real task cheaper or more deterministically.

---

## 2. PRODUCT-MARKET FIT

### Is the wedge real and defensible?

**Real, but not yet defensible.** The wedge — “LLM capabilities are too expensive, slow, and non-deterministic; bound them against user preferences” — is timely. The capability-gap framework in `docs/concepts/capability-valleys.md` is intellectually sound: focusing on *durable* gaps (where the target moves or the ground truth is un-addressable) rather than transient model weaknesses is the right moat logic.

But **defensibility is currently zero**. The moat would come from:
- a large, proprietary `descent_attempts` brain of what actually worked on real workloads (`src/teleon/evolution/descent_attempt_store.py`), and
- a library of eval harnesses and durable-gap datasets (`docs/concepts/capability-valleys.md`, `scripts/eval/durable_gap_harness.py`).

Today both are essentially empty schemas. There is no evidence of live traffic, customer workloads, or accumulated learning.

### Who buys this?

- **Primary buyer:** Engineering / AI infrastructure leads at companies already running LLMs in production and bleeding money on unpredictable frontier-model costs.
- **Secondary buyer:** Compliance / risk buyers in regulated verticals (finance, legal, healthcare, insurance) if Baltor can deliver verifiable receipts and source governance. But Baltor has no vertical focus in this pack.

### Why now?

Production LLM usage has shifted from experiments to cost/reliability/latency pressure. Model endpoints and prices change weekly. The “jagged frontier” means teams need routing, fallback, caching, and bounded behavior. That tailwind is real.

### What would kill it?

- **Incumbents add the same optimization layer.** LiteLLM, OpenRouter, LangSmith, Braintrust, Galileo, and cloud providers can all add cost/latency routing, prompt caching, and eval gates. If Teleon’s only differentiation is a registry + scoring function, it gets absorbed.
- **The “durable gap” corpus never materializes.** If most collected components become obsolete when the next model ships, the factory is producing landfill.
- **No live traffic.** Without real invocations, the descent brain stays empty and the product is just a dashboard of assertions.
- **Brand/hub sprawl confuses buyers.** `CLAUDE.md` documents a rebrand to “AI Done Right,” 22 hubs, and a private bench. To a buyer this looks like a research project, not a product.

---

## 3. WHAT’S MISSING

**A single, live, end-to-end runtime use case with measured before/after outcomes.**

They have built a meta-framework, registries, naming documents, and 470 check scripts, but there is no evidence that a real customer task actually flows through Teleon, gets bounded by a descent strategy, and produces a cheaper/faster/more-deterministic result with a receipt. The “daily factory” generates rows (`source_record`, `canonical_entity`, `object_embedding`, etc.) but no one has shown that those rows translate into a customer outcome.

The highest-leverage thing they are not doing is: **pick one concrete capability (e.g., contract clause extraction, support ticket classification, medical coding, regulatory change detection), wire it to live traffic, run it through the Teleon runtime, record real `descent_attempts`, and publish the cost/latency/determinism delta.** Everything else — more hubs, more axes, more naming — is lower leverage until that loop works.

Cite: `CLAUDE.md` (daily factory targets), `src/teleon/evolution/descent_attempt_store.py` (brain with no data), `src/teleon/evolution/substrate_selector.py` (only cost-axis downgrade), `src/teleon/storage/record_store.py` (planned streams).

---

## 4. NEXT STEPS (prioritized, most impactful first)

1. **Ship one live end-to-end capability use case.**  
   Stop expanding hubs. Pick a single high-value task, get a design partner to route real traffic through Teleon, measure before/after on cost, latency, determinism, and accuracy, and populate `descent_attempts` with real records. This is the only thing that validates the entire product thesis.

2. **Make the descent loop actually work across multiple axes.**  
   `substrate_selector.py` only does `model_downgrade()`. Implement and wire at least three working strategies — e.g., prompt/skill compression (`tokens_in`), rule/cache extraction (`determinism`), multi-provider failover (`reliability`) — with concrete substrate picks from the context/harness/skill registries. Integrate them with `src/teleon/objectives/objective.py` so the runtime adapts automatically against a tenant objective.

3. **Prove the storage tier policy at scale, or stop claiming trillions of rows.**  
   Replace the `sqlite_wal` + JSONL hand-waving in `src/teleon/storage/record_store.py` with a real history-tier loader (partitioned Parquet + ClickHouse/BigQuery) and demonstrate ingestion throughput and idempotent dedupe on a billion-row-shaped workload. If this cannot be built, shrink the claims.

4. **Build a minimal customer-facing runtime API and dashboard.**  
   A tenant should be able to submit a `CapabilityTask`, get a selection trace, and view a receipt. Build the smallest viable Teleon Control Tower / Capability Assurance Portal and put it in front of three paying or pilot customers. Cite: `docs/strategy/teleon-baltor-openharnesshub-portfolio.md`, `CLAUDE.md`.

5. **Freeze scope and finish the Baltor → Teleon extraction.**  
   Kill or merge the 22 hubs down to the 3-4 that matter, complete the runtime extraction from `src/baltor/` to `src/teleon/`, and enforce the dependency law in CI with real import checks, not just `scripts/check_portfolio_dependency_law.py`.

---

## 5. ONE BRUTAL TRUTH

**You have built an elaborate ontology to avoid running a real runtime on real customer traffic.**

The “AI Done Right” rebrand, the 22 Open*Hubs, the 470 `check_*.py` proof gates, the daily factory targets, and the locked naming stack are productivity theater. The actual product is a collection of JSON registries, Python scoring utilities, and architecture documents. `src/teleon/evolution/descent_attempt_store.py` is a dataclass with no data. `src/teleon/evolution/substrate_selector.py` is one function with a fallback constant. `src/teleon/storage/record_store.py` is sqlite. Until a live task actually flows through Teleon and the brain records real attempts, this is not a startup — it is a well-organized research project with a domain purchase history.

Cite: `CLAUDE.md`, `docs/strategy/teleon-baltor-openharnesshub-portfolio.md`, `src/teleon/evolution/descent_attempt_store.py`, `src/teleon/evolution/substrate_selector.py`, `src/teleon/storage/record_store.py`.