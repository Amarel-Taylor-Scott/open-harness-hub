"""src.teleon.evolution.descent — the PROACTIVE descent decision: how far to push a capability toward determinism.

This is the forward-facing counterpart to `src.teleon.self_healing`. Healing asks "is it still correct? restore
it." Descent asks "can it be made cheaper / more deterministic without losing what matters?" Two entry points:

  * descent_decision(...) — the objective-gated fork-vs-hold call for a non-deterministic runner (model) vs its
    distilled deterministic rule. Returns DESCEND (promote the rule) or HOLD (keep the model) per a
    CapabilityObjective, with the full SelectionTrace. Pure.
  * plan_descent_to_determinism(graph, ...) — over a capability's evolution GRAPH, the most-deterministic runner
    that still meets a coverage bar (the residual routes to a richer ancestor) + the non-det -> det spine.

Pure + deterministic; Teleon-layer — never imports src.baltor.
"""
from __future__ import annotations

from src.teleon.objectives import select

_DET_EPS = 1e-9


def descent_decision(objective, *, model_metrics, rule_metrics,
                     model_id: str = "model", rule_id: str = "distilled_rule") -> dict:
    """Objective-gated fork-vs-hold. Score the non-deterministic runner (``model_metrics``) against its distilled
    deterministic rule (``rule_metrics``) under ``objective`` and decide whether to DESCEND (promote the rule) or
    HOLD (keep the model). e.g. a cost/determinism/llm objective descends; a maximize_accuracy objective holds when
    the rule's accuracy is lower (it diverges on novel inputs). Returns the decision + the full, deterministic
    SelectionTrace. serves_truth pinned False — a descent choice is a routing decision, never a fact."""
    trace = select([(model_id, model_metrics), (rule_id, rule_metrics)], objective)
    descend = trace["chosen"] == rule_id
    return {"decision": "descend" if descend else "hold", "chosen": trace["chosen"],
            "descend": descend, "selection": trace, "serves_truth": False}


def plan_descent_to_determinism(graph, *, min_coverage: float = 0.0) -> dict:
    """Over a capability's evolution graph, the most-deterministic runner that still meets ``min_coverage`` —
    Teleon runs it for the covered cases and routes the residual to a richer ancestor (lossless, enforced by the
    graph) — plus the non-deterministic -> most-deterministic spine. serves_truth pinned False."""
    chosen = graph.most_deterministic_runner(min_coverage=min_coverage)
    spine = graph.descent_path()
    return {
        "capability_slot": graph.capability_slot,
        "chosen_runner": chosen.runner_id,
        "determinism": chosen.determinism,
        "capability_coverage": chosen.capability_coverage,
        "cost": chosen.cost,
        "fully_deterministic": chosen.determinism >= 1.0 - _DET_EPS,
        "descent_spine": [n.runner_id for n in spine],
        "min_coverage": min_coverage,
        "serves_truth": False,
    }
