# The Computational Substrate & the Foundational Law

**Status:** Owner strategy feedback 2026-06-24, reconciled into the architecture (owner granted standing authority to
modify/reconcile/improve). Machine-checked companion: `architecture/substrate_layers.json` +
`scripts/check_substrate_layers.py` (in the proof suite). This doc is the narrative; the JSON is the source of truth
for the layer↔asset↔gap map and cannot drift (every claimed asset is asserted to exist on disk).

## The reframe (agreed)

We are not designing point products. We are building a **systems layer for executable capability**:

```
Google indexes information.        Teleon indexes executable capability   (governs EFFICIENCY).
                                   Baltor governs truth                   (governs TRUTH).
                                   Open*Hubs structure machine knowledge  (discovery ≠ trust).
                                   Observer watches intelligence usage itself.
```

The Teleon/Baltor split (optimization vs verification) is correct and **permanent**. The compiler-scale framing
(intent → capability search → implementation search → optimization passes → deterministic replacement → simulation →
benchmark → execute → observe → descend) is the right altitude — "LLVM for cognition." The registry federation is
the moat substrate. None of that is in question.

## The headline finding: you already built most of it

The seven "missing layers" + Registry 100 were checked against the codebase. **8 of 8 already exist in some form**
(`check_substrate_layers.py`: 1 live · 6 partial · 1 deferred · **0 pure gaps**). Applying your own Layer-8 law to our
*own* architecture: **do not rebuild what exists — close the specific gap.**

| # | Proposed layer | Status | Already in repo | The REAL gap |
|---|---|---|---|---|
| 1 | Computational Genome / Primitives | partial | `fundamental_primitives_taxonomy.json`, `scripts/primitives/`, `knowledge/code_genome.py`, `code_genome_index.json` | the finer ~25 atomic ops as a registry + per-software decomposition (Stripe SDK → [auth, retry, parse…]) |
| 2 | Infrastructure Registry | partial | `deploy_topology.json`, `execution_backend_pricebook.json`, `capability_runtime_classes.json` (has cold_start, gpu) | unified deployment-economics across Modal/RunPod/Replicate/Fly/AWS/CF — egress, concurrency, region, cold-start-ms |
| 3 | Software Relationship Graph | partial | `knowledge/dependency_graph.py`, `repo_similarity.py`, `github_repo_harvester.py`, `harvest_tools.py` | cross-ecosystem (PyPI/npm/Docker/HF) **co-installation** stats at scale |
| 4 | Human Behavioral Registry | partial | `behavioral_heuristics.json`, `observer/capture.py`, `session_store.py` | **mining** repeated human workflows from captured sessions → automation-opportunity registry |
| 5 | AI Usage Waste Engine | **live** | `observer/` (router/review), `economics/`, `check_inefficient_pipeline_archetypes.py`, `reinvention_guard.py` | crystallize patterns into a queryable Waste Registry `{pattern, avoidable_cost, avoidable_tokens}`; grow Observer to a product |
| 6 | Universal Adapter Factory | partial | `components/adapter_factory.py` (`from_openapi` already collapses N×M→N+M) | Docker-container→component and Python-package→capability-node factories |
| 7 | Capability Futures Market | **deferred** | `eval/reason_codes.py` (durability_class, decay_signal), `inference-time-capability-watch.md` | the predictive *market* — deferred by design (see pushback) |
| 100 | Existing Systems Registry | partial | `reinvention_guard.py`, `reuse_no_reinvention_rubric.json`, the registry federation | a comprehensive existing-systems **corpus** (SaaS/enterprise/internal) feeding the guard |

The pattern is consistent: **the decision engines exist; the corpora/coverage are thin.** That is good news — the
hard architectural work is done; the remaining work is feeding and widening, which is cheaper and lower-risk.

## The Foundational Law (installed, reconciled)

Your law is adopted — and reconciled with the two selection laws already in the repo so they compose instead of
collide. Single source: `architecture/substrate_layers.json` → `foundational_law`.

1. **System filter (what WE build):** *Does this improve **compiler intelligence**? If no, don't build it.*
2. **Execution filter (the descent):** *Can intelligence be **removed** from this execution path? Descend toward
   that forever.* — already the Teleon thesis (make-it-work → make-it-cheap → deterministic substitution).
3. **Component admission (what enters the registries):** two-axis — must **LIFT** over the bare model AND the lift
   must be **STRUCTURAL/durable**. Already canonical: `capability-valleys.md` + `scripts/eval/reason_codes.py`.
4. **Binding constraint (the governor over all of the above):** **DEPTH BEFORE BREADTH.** Every new layer must serve
   the **one vertical being proven to a paying customer**, gated by `scripts/proposal_backlog.py`.

> The owner's law is **necessary**; the pre-existing laws make it **sufficient.** #1 selects what we build, #3
> selects what enters the registries, #2 is the descent, #4 subordinates all of it to revenue/depth.

The deepest line — *"the future belongs to systems that become progressively better at deciding when intelligence is
unnecessary"* — is the permanent thesis. #2 is its operational form.

## Honest pushback (the part you're paying me for)

1. **The risk you named is the real one, and your own law is the partial cure — but it isn't enough alone.** "Does
   this improve compiler intelligence?" justifies *almost everything* (every registry improves compiler
   intelligence). That filter, used alone, *causes* the breadth problem. The binding constraint (#4, depth before
   breadth) is what actually stops sprawl. The repo already shows the symptom: ~96 registries, deep scaffolding, but
   `go_live_ready=false` and **no live paying vertical yet**. The missing ingredient is **not another layer — it's
   one vertical earning revenue.** Adding 7 more layers before that is the failure mode, not the win.
2. **Capability Futures stays deferred — on purpose.** The predictive *substrate* exists (durability/decay/watch),
   and two-axis admission already *is* a futures judgment ("is this lift durable?"). A predictive *market* is
   speculative and unfalsifiable until a vertical generates the ground-truth to calibrate it. Build the watch; defer
   the market.
3. **This very turn obeyed the law.** The disciplined response to "build 7 layers" was to discover they exist and
   ship a *map + law + drift-check* (improves compiler intelligence about itself; ~zero sprawl) rather than 7
   half-built subsystems. That is the law working.

## What to actually do next (ranked by the law, not by novelty)

The **P1** gaps — each improves compiler intelligence *and* plausibly serves the proving vertical:

- **Infra deployment-economics metadata** (Layer 2) — give the compiler egress/concurrency/region/cold-start across
  the real providers so it prices *deployment*, not just inference. Concrete, bounded, high-ROI.
- **AI Waste Registry** (Layer 5) — crystallize Observer's detected patterns into the `{pattern, avoidable_cost,
  avoidable_tokens}` schema; it's the Observer's product surface and the clearest standalone wedge.
- **Existing-Systems corpus** (Layer 100) — widen what feeds `reinvention_guard`; you called this the highest-ROI
  decision engine, and it already exists — it just needs more corpus.

P2 (genome atoms, ecosystem co-installation graph, Docker/package adapter factories), P3 (human-workflow mining),
P4 (futures market) flow through `proposal_backlog.py` and only get built when they serve the proven vertical.

**The one rule for every future turn:** before building a "new" layer, run `check_substrate_layers.py` and
`scripts/codegraph.py --audit` / `reinvention_guard` — *this already exists* is the highest-ROI decision in the
architecture, including about our own work.

Related: [portfolio-guidance](./portfolio-guidance.md) · [teleon-baltor-openharnesshub-portfolio](./teleon-baltor-openharnesshub-portfolio.md) ·
[capability-valleys](../concepts/capability-valleys.md) · [teleon-observer-ai-usage-layer](./teleon-observer-ai-usage-layer.md) ·
machine map: `architecture/substrate_layers.json`.
