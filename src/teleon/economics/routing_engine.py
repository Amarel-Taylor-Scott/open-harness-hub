"""routing_engine — System 22: BGP for computation.

Picks the cheapest VIABLE route for a model/capability under the user's cost model; exploits secondary-provider
ARBITRAGE (the same/equivalent model across many providers); and REROUTES (signalling recompile) when the live economics
change. serves_truth=false — it routes compute; truth is governed by Baltor.
"""
from __future__ import annotations

from src.teleon.economics import cost_model as CM
from src.teleon.economics import economic_graph as EG
from src.teleon.inference.preference_profile import PreferenceProfile, cost_first


def route_model(model_node_id: str, *, profile: PreferenceProfile | None = None, shard: str = "000") -> dict:
    """Choose the best route for a model across its substitutable alternatives (arbitrage over providers)."""
    profile = profile or cost_first()
    routes = EG.routes_for_model(model_node_id, shard=shard)
    res = CM.choose_route(routes, profile)
    return {**res, "n_routes": len(routes), "candidates": [r["resource_id"] for r in routes]}


def arbitrage(model_node_id: str, *, profile: PreferenceProfile | None = None, shard: str = "000") -> dict:
    """The explicit arbitrage view: every equivalent provider ranked cheapest-first + the chosen route."""
    profile = profile or cost_first()
    routes = EG.routes_for_model(model_node_id, shard=shard)
    ranked = sorted(CM.score_routes(routes, profile), key=lambda rs: rs[1])
    pick = CM.choose_route(routes, profile)
    return {"ranked": [(r["resource_id"], round(s, 6)) for r, s in ranked], "chosen": pick.get("chosen"),
            "route": pick.get("route"), "reason": pick.get("reason"), "serves_truth": False}


def reroute(prev_resource_id: str, routes: list, *, profile: PreferenceProfile | None = None) -> dict:
    """After a live economic change (a price-change CDC), recompute the best route over `routes` and report whether it
    CHANGED — a changed best route is the signal to recompile the affected pipelines (capability futures)."""
    profile = profile or cost_first()
    pick = CM.choose_route(routes, profile)
    new = pick.get("chosen")
    return {"prev": prev_resource_id, "new": new, "changed": new is not None and new != prev_resource_id,
            "route": pick.get("route"), "reason": pick.get("reason"), "serves_truth": False}
