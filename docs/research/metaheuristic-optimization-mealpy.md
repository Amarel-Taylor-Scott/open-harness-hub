# Research triage — mealpy (metaheuristic optimization)

Source: https://github.com/thieu1995/mealpy · MIT · ~1.2k★ · 233 gradient-free
meta-heuristic algorithms (evolutionary · swarm · physics · human · biology ·
system · math · music). Solves continuous/discrete/combinatorial optimization,
hyperparameter tuning, feature selection, gradient-free training.

## Verdict: DOCUMENT as a low-priority candidate · do NOT integrate now · NOT a hub

Triaged against the repo's standing laws (two-axis lift gate · governance-is-the-product ·
candidate ≠ active · do-not-adopt-as-runtime · no unbounded self-rewrite).

### Where it could fit (one narrow, real seam)
A bounded, gradient-free **OptimizerProviderPort candidate** for **tuning numeric
parameters from receipts** — specifically:
- the **numeric provider-selection graph** weights (Teleon routing / OpenModelRoutingHub
  policy): minimize cost/latency subject to data-class + jurisdiction constraints, fit to
  recorded `ModelInvocationReceipt` history;
- **CapabilityTask config search** in Teleon's eval-gated candidate evaluation (bounded
  search over a declared config space, promotion still decided by evidence — NOT blind
  self-rewrite).
This is the same "wrap an adjacent mature tool as a candidate provider behind a port we
own" pattern as Temporal/mem0/etc. — never the runtime, never serving truth.

### Why it does NOT clear the bar to integrate or collect now
- **Not negative space.** Metaheuristic optimization is a mature, well-understood field;
  frontier models already reason about and apply it. It fails the *structural-lift* axis
  as a content component — it's engineering tooling, not a capability valley.
- **Speculative demand.** The numeric-provider-graph weights are currently small and
  policy-driven; there's no measured need for a 233-algorithm optimizer yet. Adopting one
  now would be solving a problem we don't have (YAGNI).

### Important: name-collision trap — it is NOT OpenOptimizationHub
**OpenOptimizationHub / Baltor's Optimize stage = CONTEXT-pack optimization** (summarize,
structure, rank, token-minimal cited packs). That is a different thing from numerical
metaheuristic optimization. mealpy must never be filed there — the word "optimization"
collides but the domains don't.

### If it ever graduates (owner-gated)
Clean MIT license (adoptable). Entry point would be a candidate entry in a Teleon
optimizer landscape (behind `OptimizerProviderPort`), gradient-free tuning of receipt-fit
policy weights, bounded + eval-gated. Until a measured need appears: **inspirational
reference only — captured here, not adopted.**
