"""cost_model — System 21: the ONE multi-objective cost function the simulator, the optimization passes, and the router
all consult. Reuses the user-weighted PreferenceProfile scorer (the multi-objective min-max weighted composite already
built + tested); turns each route's LIVE economics into a candidate, folding AVAILABILITY + SUCCESS into an EFFECTIVE cost
(a flaky / low-availability resource costs more in expectation: expected_cost = cost / (availability · success_rate)), so
we reuse the existing objective set without changing its normalization. serves_truth=false.
"""
from __future__ import annotations

from src.teleon.inference.preference_profile import PreferenceProfile, choose, score_candidates


def route_to_candidate(route: dict) -> dict:
    """Map a route's economics to a PreferenceProfile candidate (keys = the OBJECTIVES: cost/latency/tokens_in/
    determinism/freshness). Availability + success fold into an effective `cost`."""
    eco = route.get("economics", {}) or {}
    cost = float(eco.get("cost") or 0.0)
    eff = cost
    avail, succ = eco.get("availability"), eco.get("success_rate")
    if isinstance(avail, (int, float)) and avail > 0:
        eff /= float(avail)
    if isinstance(succ, (int, float)) and succ > 0:
        eff /= float(succ)
    return {"id": route.get("resource_id"), "cost": round(eff, 8), "latency": float(eco.get("latency_ms") or 0.0),
            "tokens_in": 0, "determinism": 1.0 if route.get("deterministic") else 0.0, "freshness": 1.0,
            "raw_cost": cost, "live": bool(eco.get("live")), "route": route}


def score_routes(routes: list, profile: PreferenceProfile) -> list:
    """[(route, score)] — lower score is better, per the user's weights. Empty input → []."""
    if not routes:
        return []
    scores = score_candidates([route_to_candidate(r) for r in routes], profile)
    return list(zip(routes, scores))


def choose_route(routes: list, profile: PreferenceProfile) -> dict:
    """The constraint-respecting best route (honest chosen=None + reason if none meets the hard constraints) — reuses the
    PreferenceProfile.choose() decision. Returns {chosen (resource_id), route, score, ...} or {chosen: None, reason}."""
    if not routes:
        return {"chosen": None, "reason": "no routes available", "serves_truth": False}
    cands = [route_to_candidate(r) for r in routes]
    res = choose(cands, profile)
    if res.get("chosen") is not None:
        res["route"] = res["candidate"]["route"]
    return res
