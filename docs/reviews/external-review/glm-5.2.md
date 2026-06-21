# External review — glm-5.2 (via ollama)

> CANDIDATE · serves_truth=false · external model opinion (a proposal, never trusted truth).

# Diligence Review — Open Harness Hub (Teleon + Baltor)

## 1. ARCHITECTURE

### Biggest strength
The **dependency law enforcement via code, not prose** is the single best architectural decision in this repo. `scripts/check_portfolio_dependency_law.py` over `architecture/portfolio_dependency_law.json` means the Baltor→Teleon→OpenHarnessHub direction is machine-checked, not a wiki page that rots. Combined with the `serves_truth=false` invariant threaded through every module (`record_store.py`, `descent_attempt_store.py`, `objective.py`, `substrate_selector.py`), the team has built a discipline where evidence and truth are structurally separated. Most teams talk about this; this team encoded it.

### Three most serious risks

**Risk 1: The descent "brain" is a write-only ledger with no reader.**
`src/teleon/evolution/descent_attempt_store.py` is described as "(1) the meta-learner's memory (the empirically-best strategy per before-state, computed from records) and (2) the training corpus for a model that learns to pick the descent move." But the module is a pure append-only store with `DescentAttempt` dataclass and idempotency. There is no `select_strategy_from_history()` or `best_strategy_for(before_state)` anywhere in the pack. The "brain" is currently a brain with no cortex — it accumulates and never recalls. The entire meta-learning thesis is unimplemented. This is the load-bearing claim of Teleon and it's vapor.

**Risk 2: 1427 Python modules + 470 check scripts + 124 JSON registries is a static-analysis factory, not a product.**
The repo shape itself is the risk. `CLAUDE.md` reveals the daily target: "generate 1,000 to 5,000 database-backed component candidates per day; generate 5 to 25 showcase pipelines per day." This is a content-generation pipeline dressed as architecture. The ratio of proof gates (470 `check_*.py`) to actual runtime code suggests the team is optimizing for repo self-consistency, not user outcomes. No user has ever cared about `check_ai_done_right_surface_family.py --self-test`. This is the classic premature-platforming trap: building the registry before anyone uses the thing being registered.

**Risk 3: The substrate selector has a magic constant masquerading as a fallback.**
`src/teleon/evolution/substrate_selector.py` line: `_FALLBACK_DOWNGRADE_FACTOR = 0.1`. The docstring admits this was previously a "GUESSED constant" and the fix is to source it from `architecture/model_index.json`. But the fallback IS the guessed constant, and `model_index.load_index()` reads a static JSON file — there's no live verification that the model is actually available, actually costs what the JSON says, or actually meets the quality floor. The "freshness" mechanism in `model_index.py` checks `last_verified` date against a cadence dict, but nothing actually re-verifies. The freshness system is a date comparison against a hand-edited JSON field. This is freshness theater.

---

## 2. PRODUCT-MARKET FIT

### Is the wedge real?
**No, not yet.** The wedge is described in two layers:
- **Baltor** = "context engine" (ingest→reconcile→harden→enrich→compress→serve)
- **Teleon** = "runtime that descends capabilities"

But neither has a named buyer, a named workflow, or a named pain. `docs/strategy/teleon-baltor-openharnesshub-portfolio.md` says "Baltor is powered by Teleon" — Baltor is the first tenant. That means **the first customer is yourself.** There is zero evidence in this pack of an external user, a pilot, a LOI, or a workflow someone pays for.

The "capability valleys" thesis in `docs/concepts/capability-valleys.md` is intellectually serious — the distinction between transient and durable gaps is genuinely useful. But it's a research thesis, not a product. "No-endpoint tasks" (Tier 4-5 retrievability) are real, but who is the buyer? A compliance team? A legal team? A regulatory affairs team? The pack never says.

### Who buys this?
The pack doesn't answer this. The closest signal is the "fragile-context volatility_class" in `descent_axes.py` — regulations, laws, fees, rates, prices that change. That points toward **regulatory compliance / legal ops / financial data ops** as the natural vertical. But the team hasn't committed. They're building a horizontal runtime + a horizontal context engine + an open ecosystem. Three horizontal things with no vertical wedge is not a go-to-market.

### Why now?
The only "why now" in the pack is implicit: models are getting cheaper, so the cost-descent axis (`substrate_selector.py`, `model_index.py`) is timely. But "models are getting cheaper" is a reason to NOT build infrastructure around model selection — the labs are commoditizing the routing layer themselves. OpenAI, Anthropic, Google all offer cost-tier routing natively now. Teleon's model-downgrade descent is building a layer the model providers will absorb.

### What would kill it?
1. **Model providers build cost/latency routing natively** (already happening — Anthropic's model router, OpenAI's automatic model selection). This kills the `cost` and `latency` descent axes.
2. **The team never ships a user-facing product.** 1427 modules and no "Baltor serves a query to a human user" path visible in this pack.
3. **The open ecosystem gets no contributors.** 22 Open*Hubs with no community is a graveyard, not a moat.

---

## 3. WHAT'S MISSING

**The highest-leverage thing they are NOT doing: closing the descent loop.**

The entire Teleon thesis is: take an unbounded capability → descend it to bounded/cheaper/faster. `descent_attempt_store.py` records attempts. `descent_axes.py` defines axes. `substrate_selector.py` picks a model. `objective.py` scores candidates. But **there is no `descend()` function that actually executes a descent, measures the before/after, and writes the attempt record.** The store has a writer. The axes have vocabulary. The selector has a picker. The objective has a scorer. **Nobody runs the loop.**

The team has built every component of the feedback loop except the loop itself. This is like building a Tesla's motor, battery, and chassis but never connecting the drivetrain. The "meta-learner that gets smarter over time" — the core IP claim — does not exist as executable code.

---

## 4. NEXT STEPS (prioritized)

1. **Write `src/teleon/evolution/descend.py` — the actual descent executor.** Take a CapabilityTask + a user objective, try ≥2 strategies from `descent_strategy_registry.json`, measure before/after on all axes in `descent_axes.py`, write `DescentAttempt` records, return the winner. This is the product. Everything else is scaffolding without it.

2. **Pick ONE vertical for Baltor and name the buyer.** Based on the `freshness` axis + `volatility_class` + CDC re-ingest thesis in `descent_axes.py`, the obvious wedge is **regulatory/compliance context** (rates, fees, regulations that change on known cadences). Name a customer profile, name a workflow, name a price. Stop building 22 hubs.

3. **Get one external user to call Baltor's serve endpoint.** Not a check script. Not a self-test. A human or system outside the repo issuing a query and getting a hardened, enriched, compressed context response. If this doesn't exist, the product doesn't exist.

4. **Replace `model_index.json` static freshness with a live probe.** `model_index.py`'s `apply_staleness()` compares dates in a hand-edited JSON. Add a `verify_model_entry()` that actually pings the endpoint or checks the API pricing page. Without this, the freshness axis is a paperwork exercise.

5. **Cut the Open*Hub count from 22 to 3.** OpenContextHub, OpenHarnessHub, OpenSkillsHub. Kill or freeze the other 19. 22 hubs with no contributors is anti-signal — it tells the world you can't focus. The `check_ai_done_right_surface_family.py` script that counts them is enforcing breadth at the expense of depth.

---

## 5. ONE BRUTAL TRUTH

**The team is building infrastructure for a product that doesn't exist yet, and they know it but won't admit it.**

The evidence is everywhere:
- `CLAUDE.md` says "Baltor context control is the product focus" but the daily factory target is "generate 1,000 to 5,000 component candidates per day" — that's a data pipeline, not a product.
- The portfolio has 3 product layers + 22 hubs + 124 architecture JSONs + 470 proof gates, and zero evidence of a served user query.
- `descent_attempt_store.py` calls itself "the BRAIN" but has no read path — it's a brain that can't think.
- The team has spent more effort on naming (`teleon-naming-and-domain.md`, three superseded names, a "LOCKED" date) than on shipping a user-facing endpoint.

The team is in denial that **architecture is not progress.** The dependency law, the freshness policy, the descent axes, the storage tier policy, the seven primitives — these are all genuinely well-designed. But they are the foundation of a house where nobody has poured the slab yet. The highest-risk thing in this repo is not a technical flaw; it's that the team feels productive because `--self-test` passes, while no user has ever been served. They need to stop building the factory and start building the thing the factory makes.