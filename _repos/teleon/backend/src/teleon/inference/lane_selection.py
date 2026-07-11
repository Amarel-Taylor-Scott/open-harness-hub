"""src.teleon.inference.lane_selection — choose the INFERENCE LANE by objective, bounded by org policy.

Codex, local Ollama, Gemma, the frontier APIs — these are interchangeable inference LANES behind the gateway.
This selects among them with the SAME objective layer used for runners, placement, and provider endpoints, so a
capability runs its model calls on the lane that fits the tenant's priority:
  minimize_cost -> a free local lane (Ollama)   an accuracy/capability priority -> a capable cloud lane (Codex)
The org guardrail policy can FORBID lanes before selection (safety beats objective): an air-gapped org forbids
every cloud lane, so inference falls back to local Ollama; a no-LLM org forbids every model lane (escalate).

This produces a lane PREFERENCE; src.teleon.inference.oips then handles eligibility, secrets, governed fallback,
and the ModelInvocationReceipt for the chosen lane. Pure + deterministic; reads shared DATA only; Teleon-layer —
never imports src.baltor. A lane choice is a routing decision, never a fact (serves_truth False).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path

from src.teleon.objectives import MetricVector, select

_PROFILES_PATH = _resource("architecture") / "inference_lane_profiles.json"
#: every inference lane is a (non-deterministic) model call — uniform across lanes, so it never discriminates;
#: cost / latency / capability(accuracy) are what differ. Used when policy-checking a lane (kind=model).
_LANE_DETERMINISM = 0.2


def _load(profiles: dict | None = None) -> dict:
    return profiles if profiles is not None else json.loads(_PROFILES_PATH.read_text(encoding="utf-8"))


def lanes(*, profiles: dict | None = None) -> list[dict]:
    return list(_load(profiles).get("lanes", []))


def _metric_vector(lane: dict) -> MetricVector:
    # capability -> accuracy; llm_usage uniform (all lanes are model calls) so it stays neutral.
    return MetricVector(cost=float(lane["cost"]), latency=float(lane["latency_ms"]), llm_usage=1.0,
                        determinism=_LANE_DETERMINISM, accuracy=float(lane["capability"]))


def forbidden_lanes(policy, *, profiles: dict | None = None) -> set:
    """The lane_ids an org guardrail policy disallows — a cloud lane under an air-gapped (no_external_egress)
    policy, or every model lane under a no-LLM policy. Feed into select_lane(forbidden=...)."""
    from src.teleon.governance import evaluate
    out = set()
    for lane in lanes(profiles=profiles):
        decision = evaluate({"source_domain": lane["egress_domain"], "kind": "model",
                             "determinism": _LANE_DETERMINISM, "llm_usage": 1}, policy)
        if not decision.allowed:
            out.add(lane["lane_id"])
    return out


def select_lane(objective, *, forbidden: set | None = None, profiles: dict | None = None) -> dict:
    """Pick the inference lane that best fits ``objective`` (minimize_cost -> free local; capability priority ->
    Codex/frontier), excluding policy-``forbidden`` lanes first (safety beats objective; all-forbidden fails loud
    via ObjectiveError). Returns the objective layer's full SelectionTrace + the chosen lane's detail. Never truth."""
    ls = lanes(profiles=profiles)
    candidates = [(lane["lane_id"], _metric_vector(lane)) for lane in ls]
    trace = select(candidates, objective, forbidden=forbidden)
    chosen = next(lane for lane in ls if lane["lane_id"] == trace["chosen"])
    return {**trace, "chosen_lane": chosen}
