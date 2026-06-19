"""src.teleon.evolution — PROACTIVE capability progression (non-deterministic -> most-deterministic).

This package and `src.teleon.self_healing` are deliberately SEPARATE concerns. Keep them distinct:

  evolution/    PROACTIVE. Trigger = an OPPORTUNITY (telemetry shows a deterministic fork could cover most cases
                more cheaply). Goal = PROGRESS a capability forward: fork/distill it toward determinism while
                PRESERVING coverage (lossless), and record the whole life story as a graph. Never detects breakage.
                  - capability_graph.py : the shared LINEAGE graph (runner versions + evolution edges).
                  - descent.py          : the objective-gated fork-vs-hold DECISION + the graph-based descent plan.

  self_healing/ REACTIVE. Trigger = DEGRADATION (a source changed and the benchmark now fails). Goal = RESTORE
                correctness (reheal to a candidate that re-passes the benchmark, or roll back). Never makes a
                capability cheaper or more deterministic — it brings it back to working.

They MEET in two places, by design (not by accident):
  * both reuse the shared MECHANISM in `purpose_tasks` (provision/run/adapt/promote/rollback/evaluate_health), and
  * both WRITE to the one shared lineage graph here — self-healing appends `heal` edges (via `record_heal`),
    evolution appends `fork`/`distill`/`promote`/`rollback` edges. One capability, one history, two authors.

Boundary doc: docs/architecture/teleon-self-healing-vs-evolution.md. Teleon-layer — never imports src.baltor.
"""
from src.teleon.evolution.capability_graph import (
    EDGE_DISTILL,
    EDGE_FORK,
    EDGE_HEAL,
    EDGE_KINDS,
    EDGE_PROMOTE,
    EDGE_ROLLBACK,
    CapabilityEvolutionGraph,
    EvolutionEdge,
    EvolutionError,
    RunnerNode,
    record_heal,
)
from src.teleon.evolution.descent import descent_decision, plan_descent_to_determinism
from src.teleon.evolution.descent_axes import (
    DESCENT_AXES,
    HIGHER_IS_BETTER_AXES,
    LOWER_IS_BETTER_AXES,
    descent_strategies,
    freshness_policy,
    improves,
    is_axis,
)
from src.teleon.evolution.descent_measurement import cost_speed_report, measure_descent
from src.teleon.evolution.descender import descend
from src.teleon.evolution.distiller import (
    STRATEGIES,
    STRATEGY_FRESHNESS_SYNC,
    DistillationRecord,
    choose_strategy,
    distill,
    distill_candidate,
    distill_robustness,
)
from src.teleon.evolution.impl_finder import ExternalImplSearchPort, find_implementations
from src.teleon.evolution.meta_learner import DistillationMetaLearner, class_key

__all__ = [
    "CapabilityEvolutionGraph", "RunnerNode", "EvolutionEdge", "EvolutionError",
    "EDGE_FORK", "EDGE_DISTILL", "EDGE_PROMOTE", "EDGE_ROLLBACK", "EDGE_HEAL", "EDGE_KINDS",
    "record_heal", "descent_decision", "plan_descent_to_determinism",
    "distill", "distill_candidate", "distill_robustness", "DistillationRecord", "choose_strategy", "STRATEGIES",
    "STRATEGY_FRESHNESS_SYNC", "DistillationMetaLearner", "class_key",
    "find_implementations", "ExternalImplSearchPort",
    "DESCENT_AXES", "LOWER_IS_BETTER_AXES", "HIGHER_IS_BETTER_AXES", "freshness_policy", "improves", "is_axis",
    "descent_strategies", "descend", "measure_descent", "cost_speed_report",
]
