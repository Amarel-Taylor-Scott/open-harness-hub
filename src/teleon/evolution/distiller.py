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
STRATEGY_MODEL_DOWNGRADE = "model_downgrade"  # NOT deterministic: route an open-ended/text task to a CHEAPER/smaller model (the cost win when determinism is impossible)
STRATEGY_FRESHNESS_SYNC = "freshness_sync"    # ROBUSTNESS: bind a fragile/changing-fact capability to an authoritative source + CDC sync (anti-staleness)
STRATEGIES = (STRATEGY_DIRECT_API_RULE, STRATEGY_TEMPLATE_MATCH, STRATEGY_DETERMINISTIC_EXTRACT,
              STRATEGY_PARTIAL_PLUS_RESIDUAL, STRATEGY_MODEL_DOWNGRADE, STRATEGY_FRESHNESS_SYNC)

#: illustrative one-time cost (relative units) to APPLY each strategy — the meta-learner refines these from real
#: DistillationRecords. direct/template are cheap (wrap/match); extract/partial need analysis of traces;
#: model_downgrade needs an eval to confirm the cheaper model is sufficient; freshness_sync wires source + CDC.
_DISTILL_COST = {STRATEGY_DIRECT_API_RULE: 0.05, STRATEGY_TEMPLATE_MATCH: 0.08,
                 STRATEGY_DETERMINISTIC_EXTRACT: 0.18, STRATEGY_PARTIAL_PLUS_RESIDUAL: 0.30,
                 STRATEGY_MODEL_DOWNGRADE: 0.12, STRATEGY_FRESHNESS_SYNC: 0.15}
#: ceiling bands -> the default strategy. determinism_ceiling is "how inherently deterministic the capability is".
_CEILING_DIRECT = 0.99   # >= this: it's a pure deterministic call (API/compute) — direct rule, near-full coverage
_CEILING_EXTRACT = 0.70  # >= this: most of it can be a distilled rule
_CEILING_PARTIAL = 0.40  # >= this: a rule for the easy fraction + the model for the residual
_MODEL_ROOT_DETERMINISM = 0.2
_MODEL_ROOT_COST = 0.07          # per-call cost of the undistilled frontier-model runner
_DETERMINISTIC_RULE_COST = 0.0   # a distilled deterministic rule is ~free to run
_CHEAP_MODEL_COST = 0.004        # a cheaper/smaller model lane (local Ollama / Gemma) — still a model, ~17x cheaper than frontier


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
    improvement_axes: tuple = ()   # the efficiency axes the fork improves: cost / latency / llm_usage / determinism
    serves_truth: bool = False

    def as_dict(self) -> dict:
        d = {k: getattr(self, k) for k in (
            "capability_slot", "category", "strategy", "determinism_ceiling", "per_call_cost_before",
            "per_call_cost_after", "distill_cost", "coverage", "residual_fraction", "equivalence_verified",
            "lossless", "policy_allowed", "applied", "fork_runner_id", "serves_truth")}
        d["improvement_axes"] = list(self.improvement_axes)
        return d


def choose_strategy(determinism_ceiling: float) -> str:
    """The default distillation strategy for a capability's inherent determinism (the meta-learner can override)."""
    dc = float(determinism_ceiling)
    if dc >= _CEILING_DIRECT:
        return STRATEGY_DIRECT_API_RULE
    if dc >= _CEILING_EXTRACT:
        return STRATEGY_DETERMINISTIC_EXTRACT
    if dc >= _CEILING_PARTIAL:
        return STRATEGY_PARTIAL_PLUS_RESIDUAL
    # inherently model-bound (open-ended / free-text): can't go deterministic — descend to a cheaper / smaller /
    # lower-context / faster model instead (the efficiency win when determinism is impossible).
    return STRATEGY_MODEL_DOWNGRADE


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
    if strat == STRATEGY_MODEL_DOWNGRADE:
        # EFFICIENCY descent (NOT a determinism gain): the capability stays an open-ended/text MODEL task but
        # descends to a cheaper / smaller / lower-context / faster model. determinism is unchanged; the win is
        # cost + LLM-usage (lower context) + latency. residual -> the frontier model (lossless).
        after_cost = _CHEAP_MODEL_COST
        fork = RunnerNode(f"{capability_slot}::cheaper_model@distilled", capability_slot, "cheaper_model", tier=2,
                          determinism=_MODEL_ROOT_DETERMINISM, capability_coverage=cov, cost=after_cost)
        rationale = (f"model-downgrade (efficiency): cannot be made deterministic (ceiling {determinism_ceiling}); "
                     f"route ~{int(round(cov * 100))}% of cases to a cheaper/smaller/lower-context/faster model at "
                     f"~{after_cost} vs {_MODEL_ROOT_COST}; residual -> frontier model")
        equivalence_verified = False  # a cheaper model may diverge — gated by eval, never assumed equivalent
        improvement_axes = ("cost", "latency", "llm_usage")  # cheaper + faster + lower-context; determinism NOT improved
    else:
        after_cost = _DETERMINISTIC_RULE_COST
        fork = RunnerNode(f"{capability_slot}::deterministic@distilled", capability_slot, "distilled_rule", tier=1,
                          determinism=1.0, capability_coverage=cov, cost=after_cost)
        rationale = (f"distilled via {strat}: deterministic rule covers ~{int(round(cov * 100))}% of cases "
                     f"(ceiling {determinism_ceiling}); residual -> model")
        equivalence_verified = float(determinism_ceiling) >= _CEILING_DIRECT
        improvement_axes = ("cost", "latency", "llm_usage", "determinism")  # a rule is cheaper, faster, no-LLM, AND deterministic
    g.document_fork(root.runner_id, fork, rationale=rationale)
    g.validate()

    # WITHIN CONFINES: the fork is applied only if the org policy allows this runner as a fix.
    policy_allowed = True
    if policy is not None:
        from src.teleon.governance import bounds_runner_change
        policy_allowed = bounds_runner_change(fork, policy).allowed

    record = DistillationRecord(
        capability_slot=capability_slot, category=category, strategy=strat,
        determinism_ceiling=float(determinism_ceiling), per_call_cost_before=_MODEL_ROOT_COST,
        per_call_cost_after=after_cost, distill_cost=_DISTILL_COST[strat], coverage=cov,
        residual_fraction=round(1.0 - cov, 6), equivalence_verified=equivalence_verified, lossless=True,
        policy_allowed=policy_allowed, applied=policy_allowed, fork_runner_id=fork.runner_id,
        improvement_axes=improvement_axes)
    return {"capability_slot": capability_slot, "strategy": strat, "graph": g.to_dict(),
            "record": record.as_dict(), "applied": policy_allowed, "serves_truth": False}


def distill_candidate(candidate: dict, *, policy=None, strategy: str | None = None) -> dict:
    """Convenience over a CapabilityCandidate dict (from the seeder)."""
    return distill(candidate["capability_slot"], category=candidate.get("category", "other"),
                   determinism_ceiling=candidate["determinism_ceiling"],
                   deterministic_coverage_estimate=candidate["deterministic_coverage_estimate"],
                   strategy=strategy, policy=policy)


def distill_robustness(capability_slot: str, *, category: str = "other", volatility_class: str,
                       authoritative_source: str, source_coverage: float = 0.95,
                       current_determinism: float = _MODEL_ROOT_DETERMINISM,
                       current_cost: float = _MODEL_ROOT_COST, policy=None) -> dict:
    """ROBUSTNESS / FRESHNESS descent (the anti-fragility axis). A capability that relies on FRAGILE, changing
    facts (regulations, laws, fees, rates, prices) is bound to an AUTHORITATIVE source with a sync cadence matched
    to its volatility + a CDC re-heal trigger, so it ALWAYS ingests the current facts instead of going stale. The
    synced fork is a deterministic, always-current source lookup (improving freshness + determinism + cost over a
    fragile LLM recall); the residual routes to the prior runner (lossless); a freshness 'changed' event re-heals
    it via src.teleon.self_healing.reheal_on_source_change. Held within the org's confines."""
    from src.teleon.evolution.descent_axes import freshness_policy
    fp = freshness_policy(volatility_class)
    cov = max(0.0, min(1.0, float(source_coverage)))
    g = CapabilityEvolutionGraph(capability_slot)
    root = RunnerNode(f"{capability_slot}::fragile@v1", capability_slot, "model", tier=2,
                      determinism=current_determinism, capability_coverage=1.0, cost=current_cost)
    g.add_runner(root)
    fork = RunnerNode(f"{capability_slot}::synced@robust", capability_slot, "synced_source", tier=1,
                      determinism=1.0, capability_coverage=cov, cost=_CHEAP_MODEL_COST)
    g.document_fork(root.runner_id, fork,
                    rationale=(f"freshness-sync: bind to authoritative source {authoritative_source!r} on a "
                               f"{fp['sync_cadence']} cadence + CDC re-heal (volatility {volatility_class}); an "
                               f"always-current deterministic lookup covering ~{int(round(cov * 100))}%; "
                               f"residual -> fragile model; stale answers held out, never served"))
    g.validate()

    policy_allowed = True
    if policy is not None:
        from src.teleon.governance import bounds_runner_change
        policy_allowed = bounds_runner_change(fork, policy).allowed

    record = DistillationRecord(
        capability_slot=capability_slot, category=category, strategy=STRATEGY_FRESHNESS_SYNC,
        determinism_ceiling=1.0, per_call_cost_before=current_cost, per_call_cost_after=_CHEAP_MODEL_COST,
        distill_cost=_DISTILL_COST[STRATEGY_FRESHNESS_SYNC], coverage=cov, residual_fraction=round(1.0 - cov, 6),
        equivalence_verified=True, lossless=True, policy_allowed=policy_allowed, applied=policy_allowed,
        fork_runner_id=fork.runner_id, improvement_axes=("freshness", "determinism", "cost"))
    return {"capability_slot": capability_slot, "strategy": STRATEGY_FRESHNESS_SYNC, "graph": g.to_dict(),
            "record": record.as_dict(), "freshness_policy": fp, "authoritative_source": authoritative_source,
            "applied": policy_allowed, "serves_truth": False}
