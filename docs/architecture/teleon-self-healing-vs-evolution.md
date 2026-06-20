# Teleon: self-healing vs. evolution (two concerns, one shared lineage)

These are deliberately **separate** modules with **separate logic**. Keeping them apart is the point — they
answer opposite-facing questions and fire on opposite triggers. They share exactly two things, on purpose: the
underlying mechanism (`purpose_tasks`) and the one lineage graph that records a capability's history.

| | `src/teleon/self_healing/` | `src/teleon/evolution/` |
|---|---|---|
| **Direction** | Backward — restore to working | Forward — progress toward determinism |
| **Posture** | REACTIVE | PROACTIVE |
| **Trigger** | a capability **degraded** (a source changed; the benchmark now fails) | an **opportunity** (telemetry shows a deterministic fork could cover most cases cheaper) |
| **Goal** | bring coverage/correctness **back** | make it **cheaper / more deterministic** without losing coverage |
| **Never does** | make it cheaper or more deterministic | detect or repair breakage |
| **Key call** | `reheal_on_source_change` / `benchmark_health` | `descent_decision` / `plan_descent_to_determinism` / `document_fork` |
| **Writes to the graph** | `heal` edges (via `record_heal`) | `fork` / `distill` / `promote` / `rollback` edges |

## Why this split

Earlier the boundary was muddy: both touched `adapt`/`promote`/`rollback`, and both used a "heal/fix" notion, so
it wasn't obvious which module owned what. The clean rule:

- **Healing is about TRUTH staying correct.** A scraper that silently returns garbage after a site moves is a
  *health* problem. `self_healing` detects it (the benchmark is the health check) and restores it — adapt to a
  candidate that **re-passes the whole benchmark**, or roll back. It never trades coverage for cost.
- **Evolution is about COST/DETERMINISM improving.** A capability that works but burns a model call on every
  request is an *efficiency* opportunity. `evolution` forks it toward determinism: a 100%-deterministic rule that
  covers 90% of cases is a **documented fork** — the parent model is preserved, the uncovered 10% **residual is
  routed back to it**, and the trade is recorded on the edge. It never repairs breakage.

## What they share (by design, not by accident)

1. **The mechanism** — both reuse `src/teleon/purpose_tasks` (`provision` / `run_current` / `adapt` /
   `promote` / `rollback` / `evaluate_health`). Neither re-implements promotion or rollback.
2. **The lineage** — both append to the **one** `CapabilityEvolutionGraph` for a capability. Self-healing writes
   `heal` edges through `record_heal`; evolution writes `fork`/`distill`/`promote`/`rollback` edges. One
   capability, one history book, two authors. So you can read a single graph and see *both* the repairs and the
   descents a capability has been through, in order, with full lineage and rollback targets.

## The lossless law, enforced structurally

Every descent edge in the graph is checked at construction (`CapabilityEvolutionGraph.add_edge`):

- a more-deterministic child may **only lose** coverage, never invent it;
- a child may not be **less** deterministic than its parent on a fork/distill edge;
- a **coverage-losing fork must route its residual** to a preserved runner whose coverage is at least the
  fork's — otherwise the residual would be dropped, which is a lossless-distillation violation and **fails loud**.

So "most deterministic as possible" never means "lossy": `most_deterministic_runner(min_coverage=…)` returns the
highest-determinism runner that still clears the coverage bar, and the rest always has a preserved home.

## Proofs

- `scripts/check_teleon_capability_evolution_graph.py` — the graph, documented forks, descent path,
  `most_deterministic_runner`, the lossless failures, and the `record_heal` bridge.
- `scripts/check_teleon_objective_gated_descent.py` — the objective decides whether a descent fires or is held.
- `scripts/check_purpose_task_self_heal_e2e.py` + the `self_healing` proofs — the reactive restore path.
