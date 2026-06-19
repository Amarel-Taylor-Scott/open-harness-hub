"""src.teleon.evolution.descender — the GENERIC descender: improve a capability along ANY registered descent axis.

determinism / cost / latency / llm_usage are produced by the distiller's distill(); freshness by
distill_robustness(). THIS handles the trust / robustness / openness axes (verifiability, reliability, locality,
specialization, privacy, reproducibility, portability, resilience, energy, safety) UNIFORMLY from
architecture/descent_strategy_registry.json: for an axis it builds a fork that improves it, binds the machinery the
registry names, checks the fork against the org policy, and emits a DistillationRecord. Adding a new axis is a
registry entry (+ a DESCENT_AXES entry) — not new code. Lossless (parent preserved); a fork is a candidate, never
truth. Pure + deterministic; Teleon-layer — never imports src.baltor.
"""
from __future__ import annotations

from src.teleon.evolution.capability_graph import CapabilityEvolutionGraph, RunnerNode
from src.teleon.evolution.descent_axes import descent_strategies
from src.teleon.evolution.distiller import _MODEL_ROOT_COST, _MODEL_ROOT_DETERMINISM, DistillationRecord

_DESCENT_APPLY_COST = 0.10  # one-time cost to apply a generic descent (wire the binding + an eval) — refined by the meta-learner


def descend(capability_slot: str, axis: str, *, category: str = "other",
            parent_determinism: float = _MODEL_ROOT_DETERMINISM, parent_cost: float = _MODEL_ROOT_COST,
            coverage: float = 1.0, policy=None, registry: dict | None = None) -> dict:
    """Improve ``capability_slot`` along ``axis`` using the registered strategy. Builds a fork (improved on the
    axis, determinism/coverage non-regressing so the evolution-graph edge is valid), checks the org ``policy``, and
    returns the graph + DistillationRecord + the strategy's binding/reuses/measurement metadata."""
    strategies = descent_strategies(registry=registry)
    if axis not in strategies:
        raise KeyError(f"no descent strategy registered for axis {axis!r}; have: {sorted(strategies)}")
    s = strategies[axis]
    cov = max(0.0, min(1.0, float(coverage)))
    det = min(1.0, max(0.0, parent_determinism + float(s.get("fork_determinism_delta", 0.0))))
    cost = max(0.0, parent_cost + float(s.get("fork_cost_delta", 0.0)))

    g = CapabilityEvolutionGraph(capability_slot)
    root = RunnerNode(f"{capability_slot}::base@v1", capability_slot, "model", tier=2,
                      determinism=parent_determinism, capability_coverage=1.0, cost=parent_cost)
    g.add_runner(root)
    fork = RunnerNode(f"{capability_slot}::{s['fork_kind']}@descended", capability_slot, s["fork_kind"], tier=2,
                      determinism=det, capability_coverage=cov, cost=cost)
    g.document_fork(root.runner_id, fork,
                    rationale=(f"descend on {axis} via {s['strategy_id']}: {s['note']} binds: {s['binds']}; "
                               f"reuses: {s['reuses']}; governed by: {s['governed_by']}"))
    g.validate()

    policy_allowed = True
    if policy is not None:
        from src.teleon.governance import bounds_runner_change
        policy_allowed = bounds_runner_change(fork, policy).allowed

    record = DistillationRecord(
        capability_slot=capability_slot, category=category, strategy=s["strategy_id"], determinism_ceiling=det,
        per_call_cost_before=parent_cost, per_call_cost_after=cost, distill_cost=_DESCENT_APPLY_COST, coverage=cov,
        residual_fraction=round(1.0 - cov, 6), equivalence_verified=False, lossless=True,
        policy_allowed=policy_allowed, applied=policy_allowed, fork_runner_id=fork.runner_id,
        improvement_axes=tuple(s["improves"]))
    return {"capability_slot": capability_slot, "axis": axis, "strategy": s["strategy_id"], "fork_kind": s["fork_kind"],
            "improves": list(s["improves"]), "binds": s["binds"], "reuses": s["reuses"],
            "governed_by": s["governed_by"], "measurement": s["measurement"], "graph": g.to_dict(),
            "record": record.as_dict(), "applied": policy_allowed, "serves_truth": False}
