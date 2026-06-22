"""routing_engine — System 22: BGP for computation.

Picks the cheapest VIABLE route for a model/capability under the user's cost model; exploits secondary-provider
ARBITRAGE (the same/equivalent model across many providers); and REROUTES (signalling recompile) when the live economics
change. serves_truth=false — it routes compute; truth is governed by Baltor.
"""
from __future__ import annotations

from src.teleon.economics import cost_model as CM
from src.teleon.economics import economic_graph as EG
from src.teleon.inference.preference_profile import PreferenceProfile, cost_first


def reliability(route: dict) -> float:
    """availability × success_rate (1.0 when unobserved). The uptime term OpenRouter makes first-class — the cheapest
    provider saturates/degrades first, so a route that is failing must be skipped, not just priced in."""
    eco = route.get("economics", {}) or {}
    a, s = eco.get("availability"), eco.get("success_rate")
    return (float(a) if isinstance(a, (int, float)) else 1.0) * (float(s) if isinstance(s, (int, float)) else 1.0)


def viable_routes(routes: list, *, min_reliability: float = 0.0) -> list:
    """Skip recently-failing routes (reliability below the floor) BEFORE choosing — OpenRouter's stability rule."""
    return [r for r in routes if reliability(r) >= min_reliability]


def balance_weights(routes: list, *, min_reliability: float = 0.0) -> dict:
    """Distribute load across HEALTHY survivors by reliability ÷ price² (OpenRouter's inverse-square-of-price, modulated
    by uptime) — balances cost against availability instead of dumping all traffic on the cheapest (which then saturates
    and degrades first). Returns {resource_id: weight in 0..1}. A free/local route gets a large finite weight."""
    surv = viable_routes(routes, min_reliability=min_reliability)
    raw = []
    for r in surv:
        c = float((r.get("economics", {}) or {}).get("cost") or 0.0)
        price_term = (1.0 / (c * c)) if c > 0 else 1.0e6
        raw.append((r["resource_id"], reliability(r) * price_term))
    tot = sum(w for _, w in raw) or 1.0
    return {rid: round(w / tot, 6) for rid, w in raw}


def route_model(model_node_id: str, *, profile: PreferenceProfile | None = None, min_reliability: float = 0.0,
                shard: str = "000") -> dict:
    """Choose the best route for a model across its substitutable alternatives (arbitrage over providers), AFTER skipping
    routes that are failing below the reliability floor (so we never route to a degrading provider)."""
    profile = profile or cost_first()
    all_routes = EG.routes_for_model(model_node_id, shard=shard)
    routes = viable_routes(all_routes, min_reliability=min_reliability)
    res = CM.choose_route(routes, profile)
    return {**res, "n_routes": len(routes), "n_skipped_unreliable": len(all_routes) - len(routes),
            "candidates": [r["resource_id"] for r in routes]}


def arbitrage(model_node_id: str, *, profile: PreferenceProfile | None = None, min_reliability: float = 0.0,
              shard: str = "000") -> dict:
    """The explicit arbitrage view: healthy equivalent providers ranked cheapest-first + the chosen route + the load
    weights (so traffic can be spread, not all dumped on the cheapest)."""
    profile = profile or cost_first()
    routes = viable_routes(EG.routes_for_model(model_node_id, shard=shard), min_reliability=min_reliability)
    ranked = sorted(CM.score_routes(routes, profile), key=lambda rs: rs[1])
    pick = CM.choose_route(routes, profile)
    return {"ranked": [(r["resource_id"], round(s, 6)) for r, s in ranked], "chosen": pick.get("chosen"),
            "route": pick.get("route"), "weights": balance_weights(routes, min_reliability=min_reliability),
            "reason": pick.get("reason"), "serves_truth": False}


def reroute(prev_resource_id: str, routes: list, *, profile: PreferenceProfile | None = None) -> dict:
    """After a live economic change (a price-change CDC), recompute the best route over `routes` and report whether it
    CHANGED — a changed best route is the signal to recompile the affected pipelines (capability futures)."""
    profile = profile or cost_first()
    pick = CM.choose_route(routes, profile)
    new = pick.get("chosen")
    return {"prev": prev_resource_id, "new": new, "changed": new is not None and new != prev_resource_id,
            "route": pick.get("route"), "reason": pick.get("reason"), "serves_truth": False}
