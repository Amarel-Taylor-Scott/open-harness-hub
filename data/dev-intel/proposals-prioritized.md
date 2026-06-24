# Prioritized proposal backlog (development plane; serves_truth=false)

4846 proposals. The loop FILES these when it's uncomfortable applying directly; you prioritize.

Score = value x confidence x reversibility / (effort x risk). Higher = do sooner.

## ⛔ Owner decision required (brand/pricing/structure/strategy)
- **[0.9]** (proposal) [arch-narrative] LOCK the moat split: Baltor governs TRUTH; Teleon governs EFFICIENCY (descent brain). Stop both claiming governance  ·  _from the 3-reviewer architecture audit 2026-06-21_
- **[0.72]** (proposal) [arch-narrative] ratify two-products vs three-layers once (3-layer is locked+enforced; retire the two-products framing)  ·  _from the 3-reviewer architecture audit 2026-06-21_
- **[0.4267]** (proposal) [arch-overlap] define the proof-authority gate between teleon-demos and OpenHarnessHub (who owns measured proof)  ·  _from the 3-reviewer architecture audit 2026-06-21_
- **[0.4267]** (proposal) [arch-overlap] operational gate for OpenContextHub vs OpenCurrentContextHub (truth != freshness signal)  ·  _from the 3-reviewer architecture audit 2026-06-21_
- **[0.35]** (proposal) [arch-overlap] split the 5 Baltor method-hubs vs Baltor pipeline: pure-registry OR pure-workflow (clear API boundary)  ·  _from the 3-reviewer architecture audit 2026-06-21_
- **[0.32]** (plan) [plane:ai-done-right] Review: `ai-done-right [live]` — Scoping & Seams  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (risk) [wedge:ai-done-right] We need review a wedge. User asks: Review this wedge for improvement opportunities. Lens: is the wedge sharp, defensible  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (risk) [plane:baltor] Assessment  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (risk) [plane:openharnesshub] We need review one aspect of governed AI platform: Baltor context engine + Teleon thin control plane. Unit is SURFACE op  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (proposal) [arch-overlap] decide the OpenSkillToTool / OpenToolToSkillHub merge path (forward vs bidirectional)  ·  _from the 3-reviewer architecture audit 2026-06-21_
- **[0.32]** (plan) [module:src/teleon/frameworks/framework_adapters] We need review module. User provided a stub-like module with docstring and function signatures, no body. Need find concr  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (risk) [module:src/teleon/runtime/execution_providers/p] Here are the concrete improvement opportunities for this module, focusing on code quality, abstraction, and governance:  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (proposal) [module:src/baltor/adapters/object_store/local_o] 1. OPPORTUNITY: Missing base class/interface for swappability. `LocalContentAddressedObjectStore` is a concrete adapter   ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (risk) [module:src/baltor/context_audit/optimizer.py] Review: `src/baltor/context_audit/optimizer.py`  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (proposal) [module:src/baltor/experiments/parallel_paths.py] Review: `src/baltor/experiments/parallel_paths.py`  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (proposal) [module:src/baltor/experiments/path_costing.py] This module is **not solid**: it is an empty file whose docstring claims it is a functional re-export shim. That makes i  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (plan) [module:src/baltor/ports/execution_provider.py] 1. **OPPORTUNITY (Missing Implementation)**: The module is currently just a docstring. A "re-export shim" with no actual  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (risk) [plane:openharnesshub] The user wants me to review a "plane" (component/layer) called "openharnesshub" in the context of a governed AI platform  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (proposal) [architecture:taxonomy] Taxonomy & Registry Architecture Review  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (proposal) [module:src/teleon/evolution/substrate_selector.] From the stub shown, this unit is **not solid yet** — it’s an untyped, single-function module with a placeholder constan  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (risk) [module:src/teleon/experiments/parallel_paths.py] Here are 5 concrete improvement opportunities for the `parallel_paths` module, balancing bottom-up code quality with top  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (proposal) [module:src/teleon/experiments/path_promotion.py] The user wants a review of a specific Python module (`path_promotion.py`) within a governed AI platform context. The rev  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (proposal) [module:src/baltor/distillation/rehydration.py] This is **not solid** — it is two unimplemented function signatures with ambiguous semantics and no governance surface.   ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (risk) [module:src/baltor/observability/projections/lin] Here are 5 concrete improvement opportunities based on the module's structure and signatures:  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
- **[0.32]** (risk) [module:src/baltor/workers/execution_providers/c] Review: `container_image_emulator.py`  ·  _touches owner-gated surface (brand/pricing/structure/strategy)_
  … (+96 more)

## 🟡 Proposed — review then apply (riskier / not trivial)
- **[0.6]** (plan) [arch-flex] single-source the surface layer + 22-hub roster (one canonical file) + a consistency check; scattered across 4-5 files today  ·  _from the 3-reviewer architecture audit 2026-06-21_
- **[0.6]** (plan) [arch-flex] single-source tenant id baltor-internal (hardcoded ~9x) into one constant  ·  _from the 3-reviewer architecture audit 2026-06-21_
- **[0.54]** (plan) [arch-flex] finish the search-provider selector (registry exists; real_steps hardcodes Wikipedia/Ollama)  ·  _from the 3-reviewer architecture audit 2026-06-21_
- **[0.5333]** (plan) [yc-gap:traction_design_partner] secure 1 design partner + a paid pilot that EXPORTS a package consumed by their own agent/RAG, with a before/after report (the 90-day bottleneck) — owner GTM  ·  _YC readiness 0.667: no signed design partner / paid pilot_
- **[0.48]** (plan) [arch-flex] make execution-provider factory registry-driven (importlib) so a new backend is a data entry, not a code edit  ·  _from the 3-reviewer architecture audit 2026-06-21_
- **[0.4267]** (plan) [yc-gap:backends_green] run the health flywheel until gates are green: ./loop run  (or scripts/flywheel_orchestrator.py --run)  ·  _YC readiness 0.667: core proof gates: unknown_
- **[0.4267]** (plan) [yc-gap:founder_market_fit] fill the founder/team story — why you know this better than anyone + the hardest thing you've built — owner  ·  _YC readiness 0.667: founder/team story UNFILLED (the critical blocker)_
- **[0.4267]** (plan) [arch-flex] extract a StorageBackendPort for ledger + blackboard (SQLite-locked today; Git is already ported) -> customer-managed DB  ·  _from the 3-reviewer architecture audit 2026-06-21_
- **[0.32]** (opportunity) [module:src/teleon/compiler/fixtures.py] 1. **OPPORTUNITY:** `fixtures.py` mixes deterministic test fixtures with production live-state I/O. A module named `fixt  ·  _default: propose for review (not clearly trivial)_
- **[0.32]** (risk) [integration:architecture/agent_environment_research_] We need review integration architecture/agent_environment_research_registry.json. Need find concrete actionable improvem  ·  _default: propose for review (not clearly trivial)_
- **[0.32]** (plan) [research:context layer for AI agents] Outward Scan: Competitor & White-Space Analysis  ·  _default: propose for review (not clearly trivial)_
- **[0.32]** (plan) [research:context layer for AI agents] We need review research for improvement opportunities. Lens: OUTWARD scan: competitor/similar product, what they do that  ·  _default: propose for review (not clearly trivial)_
- **[0.32]** (opportunity) [research:context layer for AI agents] Outward Scan: Context-Layer Competitors  ·  _default: propose for review (not clearly trivial)_
- **[0.32]** (plan) [research:context layer for AI agents] We need review research for improvement opportunities. User asks: Lens: OUTWARD scan: is this a competitor/similar produ  ·  _default: propose for review (not clearly trivial)_
- **[0.32]** (plan) [plane:ai-done-right] This plane is **not coherently scoped** against Baltor and Teleon. Right now `ai-done-right` is a fat holding brand that  ·  _default: propose for review (not clearly trivial)_
- **[0.32]** (risk) [wedge:ai-done-right] Assessment: This is a portfolio narrative, not a wedge.  ·  _default: propose for review (not clearly trivial)_
- **[0.32]** (risk) [plane:baltor] We need review one aspect of governed AI platform Baltor context engine + Teleon thin control plane. User provided a "pl  ·  _default: propose for review (not clearly trivial)_
- **[0.32]** (plan) [wedge:teleon] OPPORTUNITY 1: "AI agents" as primary buyers is a fatal GTM flaw.  ·  _default: propose for review (not clearly trivial)_
- **[0.32]** (plan) [logjam fork · glm-5.2] 1. My Read of the Problem  ·  _logjam: no new findings for 4 cycles; the K8s live-dispatch path is blocked_
- **[0.32]** (plan) [logjam fork · kimi-k2.7-code] We need answer as expert pair for stuck engineer. User asks: teammate (Claude) stuck. Question: improvement lo  ·  _logjam: no new findings for 4 cycles; the K8s live-dispatch path is blocked_
- **[0.32]** (plan) [yc-gap:decisions_locked] owner: ratify raise size + pricing + lock the one-liner (owner-gated decisions)  ·  _YC readiness 0.667: raise/pricing/one-liner not ratified_
- **[0.32]** (opportunity) [wedge:openharnesshub] Verdict:** The wedge is **not sharp yet**. “Open ecosystem + open spec” is a *category*, not a point of insertion. The b  ·  _default: propose for review (not clearly trivial)_
- **[0.32]** (risk) [plane:open-star-hubs] Open*Hubs — Registry Surfaces Feeding Teleon's Selection Substrate  ·  _default: propose for review (not clearly trivial)_
- **[0.32]** (risk) [wedge:open-star-hubs] We need review a wedge for improvement opportunities. Need act as senior staff engineer + product/design lead. Need asse  ·  _default: propose for review (not clearly trivial)_
- **[0.32]** (risk) [plane:teleon-demos] Review: teleon-demos surface  ·  _default: propose for review (not clearly trivial)_
  … (+3283 more)

## 🟢 Auto-eligible (trivial + reversible — the autofix/agent can apply)
- **[1.6]** (risk) [module:src/teleon/agents/agent_runtime_provider] We need review module based only on API signatures and call edges. Need find concrete actionable improvement opportuniti  ·  _trivial + reversible_
- **[1.6]** (risk) [module:src/teleon/blackboard/local_sqlite_black] We need review module based on API signatures and call edges only, no code body. User asks concrete actionable improveme  ·  _trivial + reversible_
- **[1.6]** (plan) [module:src/teleon/blackboard/token_economics.py] We need review module token_economics.py. We have only API signatures and call edges, not code. Need find concrete actio  ·  _trivial + reversible_
- **[1.6]** (opportunity) [module:src/teleon/compiler/__main__.py] Review: `src/teleon/compiler/__main__.py`  ·  _trivial + reversible_
- **[1.6]** (risk) [module:src/teleon/compiler/compile.py] Here are 5 concrete improvement opportunities for the `compile.py` module:  ·  _trivial + reversible_
- **[1.6]** (risk) [plane:teleon] We need review one aspect of governed AI platform: Teleon thin control plane. Need find concrete actionable improvement   ·  _trivial + reversible_
- **[1.6]** (risk) [wedge:teleon] We need review one aspect of governed AI platform wedge. Need be senior staff engineer + product/design lead. Need concr  ·  _trivial + reversible_
- **[1.6]** (plan) [architecture:hierarchies] Assessment  ·  _trivial + reversible_
- **[1.6]** (plan) [module:src/teleon/egress/policy.py] We need review module src/teleon/egress/policy.py. We only have stub signatures and dependency graph. Need find concrete  ·  _trivial + reversible_
- **[1.6]** (plan) [module:src/teleon/egress/transports.py] The user wants a review of a module `src/teleon/egress/transports.py` with a specific lens: code quality (bugs, fragilit  ·  _trivial + reversible_
- **[1.6]** (opportunity) [module:src/teleon/enrichment/search_enrich.py] Review: `src/teleon/enrichment/search_enrich.py`  ·  _trivial + reversible_
- **[1.6]** (risk) [module:src/teleon/environments/baltor_cfpb_cont] We need review module. We have only stub signatures and docstring. Need find concrete actionable improvement opportuniti  ·  _trivial + reversible_
- **[1.6]** (risk) [module:src/teleon/environments/local_environmen] Review: `local_environment_provider.py`  ·  _trivial + reversible_
- **[1.6]** (opportunity) [module:src/teleon/environments/reward_runner.py] Review: `reward_runner.py`  ·  _trivial + reversible_
- **[1.6]** (risk) [module:src/teleon/evolution/catalog_descent.py] Here are the concrete improvement opportunities for `catalog_descent.py`, based on the module's interface, call graph, a  ·  _trivial + reversible_
- **[1.6]** (opportunity) [module:src/teleon/evolution/catalog_descent.py] We need review module. We have only stub signatures and docstring, no actual code. Need produce improvement opportunitie  ·  _trivial + reversible_
- **[1.6]** (opportunity) [module:src/teleon/evolution/descender.py] Review: `src/teleon/evolution/descender.py`  ·  _trivial + reversible_
- **[1.6]** (risk) [module:src/teleon/evolution/descent.py] Review: `src/teleon/evolution/descent.py`  ·  _trivial + reversible_
- **[1.6]** (risk) [module:src/teleon/evolution/descent.py] The user wants me to review a module called `src/teleon/evolution/descent.py` from their governed AI platform (Baltor co  ·  _trivial + reversible_
- **[1.6]** (opportunity) [module:src/teleon/evolution/descent_attempt_sto] Verdict: not solid.** The module docstring literally advertises itself as “the BRAIN + data store,” which is the core sm  ·  _trivial + reversible_
- **[1.6]** (risk) [module:src/teleon/evolution/descent_axes.py] We need review module. Need be senior staff engineer. Need concrete actionable improvements. Lens: code quality bugs, fr  ·  _trivial + reversible_
- **[1.6]** (risk) [module:src/teleon/evolution/distiller.py] The module shape is **procedural, constant-heavy, and seam-poor**: strategy names are plain strings, costs/ceilings are   ·  _trivial + reversible_
- **[1.6]** (plan) [module:src/teleon/experiments/path_comparator.p] We need review module path_comparator.py. User provided only signatures and call graph, no actual code body. We need fin  ·  _trivial + reversible_
- **[1.6]** (risk) [module:src/teleon/experiments/path_promotion.py] This module is **not solid** as shown. The signatures reveal a governance-critical component (the sole promotion authori  ·  _trivial + reversible_
- **[1.6]** (plan) [module:src/teleon/exploration/dispatch.py] We need review module src/teleon/exploration/dispatch.py. User provided only signatures and docstring, no actual code bo  ·  _trivial + reversible_
  … (+1392 more)

