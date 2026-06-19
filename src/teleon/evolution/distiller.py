"""src.teleon.evolution.distiller — distill an unbounded capability toward 'as deterministic as possible, within
confines'.

Given a capability candidate (its determinism_ceiling + deterministic_coverage_estimate), this produces the FIRST
real DETERMINISTIC FORK on its evolution graph and a DistillationRecord. The fork is the cheap, fully-deterministic
runner that covers the deterministic fraction of cases; the uncovered residual is ROUTED to the preserved model
(lossless — the parent is never deleted, held-out cases keep a home). The fork must pass the org guardrail policy
('within confines') — if it would cross the org's rules, the distillation is HELD and escalates instead.

The DistillationRecord captures what the meta-learner optimizes: the one-time DISTILL COST (by strategy), the
per-call cost DROP (model -> ~0 deterministic), the coverage achieved, and whether the covered cases are verified
equivalent. Doing this cheaply + at scale is the moat; the record is the evidence that lets it get cheaper.

Pure + deterministic; Teleon-layer — never imports src.baltor. A fork/record is a routing + lineage artifact,
never a fact (serves_truth False).
"""
from __future__ import annotations

from dataclasses import dataclass

from src.teleon.evolution.capability_graph import CapabilityEvolutionGraph, RunnerNode

#: distillation strategies, cheapest-to-apply first. The strategy decides HOW the deterministic rule is produced.
STRATEGY_DIRECT_API_RULE = "direct_api_rule"            # the capability IS a deterministic call -> wrap it (cheapest, ~full coverage)
STRATEGY_TEMPLATE_MATCH = "template_match"              # an exact-match template for the canonical sub-cases
STRATEGY_DETERMINISTIC_EXTRACT = "deterministic_extract"  # distill a rule from verified traces for most cases
STRATEGY_PARTIAL_PLUS_RESIDUAL = "partial_rule_plus_model_residual"  # rule for the easy fraction, model for the rest
STRATEGIES = (STRATEGY_DIRECT_API_RULE, STRATEGY_TEMPLATE_MATCH, STRATEGY_DETERMINISTIC_EXTRACT,
              STRATEGY_PARTIAL_PLUS_RESIDUAL)

#: illustrative one-time cost (relative units) to APPLY each strategy — the meta-learner refines these from real
#: DistillationRecords. direct/template are cheap (wrap/match); extract/partial need analysis of traces.
_DISTILL_COST = {STRATEGY_DIRECT_API_RULE: 0.05, STRATEGY_TEMPLATE_MATCH: 0.08,
                 STRATEGY_DETERMINISTIC_EXTRACT: 0.18, STRATEGY_PARTIAL_PLUS_RESIDUAL: 0.30}
#: ceiling bands -> the default strategy. determinism_ceiling is "how inherently deterministic the capability is".
_CEILING_DIRECT = 0.99   # >= this: it's a pure deterministic call (API/compute) — direct rule, near-full coverage
_CEILING_EXTRACT = 0.70  # >= this: most of it can be a distilled rule
_CEILING_PARTIAL = 0.40  # >= this: a rule for the easy fraction + the model for the residual
_MODEL_ROOT_DETERMINISM = 0.2
_MODEL_ROOT_COST = 0.07          # per-call cost of the undistilled model runner
_DETERMINISTIC_RULE_COST = 0.0   # a distilled deterministic rule is ~free to run


@dataclass(frozen=True)
class DistillationRecord:
    """The evidence of one distillation — what the meta-learner learns from. ``distill_cost`` is the one-time
    cost of applying the strategy; ``per_call_cost_before/after`` is the recurring saving; ``coverage`` is the
    fraction the deterministic rule handles; ``residual_fraction`` routes to the preserved model."""
    capability_slot: str
    category: str
    strategy: str
    determinism_ceiling: float
    per_call_cost_before: float
    per_call_cost_after: float
    distill_cost: float
    coverage: float
    residual_fraction: float
    equivalence_verified: bool
    lossless: bool
    policy_allowed: bool
    applied: bool
    fork_runner_id: str
    serves_truth: bool = False

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "capability_slot", "category", "strategy", "determinism_ceiling", "per_call_cost_before",
            "per_call_cost_after", "distill_cost", "coverage", "residual_fraction", "equivalence_verified",
            "lossless", "policy_allowed", "applied", "fork_runner_id", "serves_truth")}


def choose_strategy(determinism_ceiling: float) -> str:
    """The default distillation strategy for a capability's inherent determinism (the meta-learner can override)."""
    dc = float(determinism_ceiling)
    if dc >= _CEILING_DIRECT:
        return STRATEGY_DIRECT_API_RULE
    if dc >= _CEILING_EXTRACT:
        return STRATEGY_DETERMINISTIC_EXTRACT
    if dc >= _CEILING_PARTIAL:
        return STRATEGY_PARTIAL_PLUS_RESIDUAL
    return STRATEGY_TEMPLATE_MATCH


def distill(capability_slot: str, *, category: str = "other", determinism_ceiling: float,
            deterministic_coverage_estimate: float, strategy: str | None = None, policy=None) -> dict:
    """Produce the deterministic fork for one capability and its DistillationRecord. Builds the evolution graph
    (model root -> deterministic rule fork, residual -> model), checks the fork against the org guardrail
    ``policy`` (the fork is APPLIED only if it stays within confines; otherwise HELD), and records the cost/
    coverage/equivalence evidence. ``strategy`` overrides the default (the meta-learner supplies the best one)."""
    strat = strategy or choose_strategy(determinism_ceiling)
    cov = max(0.0, min(1.0, float(deterministic_coverage_estimate)))
    g = CapabilityEvolutionGraph(capability_slot)
    root = RunnerNode(f"{capability_slot}::model@v1", capability_slot, "model", tier=2,
                      determinism=_MODEL_ROOT_DETERMINISM, capability_coverage=1.0, cost=_MODEL_ROOT_COST)
    g.add_runner(root)
    fork = RunnerNode(f"{capability_slot}::deterministic@distilled", capability_slot, "distilled_rule", tier=1,
                      determinism=1.0, capability_coverage=cov, cost=_DETERMINISTIC_RULE_COST)
    g.document_fork(root.runner_id, fork, rationale=(f"distilled via {strat}: deterministic rule covers "
                    f"~{int(round(cov * 100))}% of cases (ceiling {determinism_ceiling}); residual -> model"))
    g.validate()

    # WITHIN CONFINES: the fork is applied only if the org policy allows this runner as a fix.
    policy_allowed = True
    if policy is not None:
        from src.teleon.governance import bounds_runner_change
        policy_allowed = bounds_runner_change(fork, policy).allowed

    # for a pure deterministic call (ceiling ~1.0) the covered cases are exactly equivalent to the model output.
    equivalence_verified = float(determinism_ceiling) >= _CEILING_DIRECT
    record = DistillationRecord(
        capability_slot=capability_slot, category=category, strategy=strat,
        determinism_ceiling=float(determinism_ceiling), per_call_cost_before=_MODEL_ROOT_COST,
        per_call_cost_after=_DETERMINISTIC_RULE_COST, distill_cost=_DISTILL_COST[strat], coverage=cov,
        residual_fraction=round(1.0 - cov, 6), equivalence_verified=equivalence_verified, lossless=True,
        policy_allowed=policy_allowed, applied=policy_allowed, fork_runner_id=fork.runner_id)
    return {"capability_slot": capability_slot, "strategy": strat, "graph": g.to_dict(),
            "record": record.as_dict(), "applied": policy_allowed, "serves_truth": False}


def distill_candidate(candidate: dict, *, policy=None, strategy: str | None = None) -> dict:
    """Convenience over a CapabilityCandidate dict (from the seeder)."""
    return distill(candidate["capability_slot"], category=candidate.get("category", "other"),
                   determinism_ceiling=candidate["determinism_ceiling"],
                   deterministic_coverage_estimate=candidate["deterministic_coverage_estimate"],
                   strategy=strategy, policy=policy)
