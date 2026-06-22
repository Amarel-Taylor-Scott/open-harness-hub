"""simulator — System 12 (the SIMULATE stage): estimate a candidate DAG's cost / latency / quality from component
economics WITHOUT executing it, so beam search (System 5) can rank many candidates cheaply and only the top-k are
benchmarked on real data. Reads the live economic graph (merged economics per resource) + the unified cost model.

Cost is additive (you pay for every node). Latency is the CRITICAL PATH (longest path by per-node latency) so parallel
branches are modelled correctly, matching the executor's data-flow parallelism. Quality is the product of per-node
qualities (independent-degradation estimate). serves_truth=false (an estimate the benchmark stage then confirms).
"""
from __future__ import annotations

from collections import deque

from src.teleon.economics import cost_model as CM
from src.teleon.economics import economic_graph as EG
from src.teleon.inference.preference_profile import PreferenceProfile, cost_first


def _critical_path_latency(lat: dict, edges: list) -> float:
    """Longest path through the DAG by per-node latency. No edges → conservative linear sum (unknown ordering)."""
    if not edges:
        return float(sum(lat.values()))
    succ: dict = {}
    indeg = {n: 0 for n in lat}
    for a, b in edges:
        if a in lat and b in lat:
            succ.setdefault(a, []).append(b)
            indeg[b] = indeg.get(b, 0) + 1
    order, q = [], deque([n for n in lat if indeg.get(n, 0) == 0])
    indeg2 = dict(indeg)
    while q:
        u = q.popleft()
        order.append(u)
        for v in succ.get(u, []):
            indeg2[v] -= 1
            if indeg2[v] == 0:
                q.append(v)
    dist = dict(lat)
    for u in order:
        for v in succ.get(u, []):
            dist[v] = max(dist[v], dist[u] + lat[v])
    return float(max(dist.values())) if dist else 0.0


def simulate_dag(nodes: list, edges: list | None = None, *, shard: str = "000") -> dict:
    """nodes: [{step, resource_id|component|plane, deterministic?}]; edges: [[step_a, step_b]]. Returns the estimate:
    total_cost (sum, effective), total_latency_ms (critical path), est_quality (product), per_node breakdown."""
    edges = edges or []
    per, lat = [], {}
    total_cost, quality = 0.0, 1.0
    for n in nodes:
        rid = n.get("resource_id") or n.get("component") or n.get("plane")
        eco = EG.merged_economics(rid, shard=shard) if rid else {}
        cand = CM.route_to_candidate({"resource_id": rid, "deterministic": n.get("deterministic"), "economics": eco})
        total_cost += cand["cost"]
        lat[n.get("step", rid)] = cand["latency"]
        q = eco.get("quality")
        if isinstance(q, (int, float)):
            quality *= float(q)
        per.append({"step": n.get("step"), "resource_id": rid, "cost": cand["cost"], "latency": cand["latency"], "live": cand["live"]})
    return {"total_cost": round(total_cost, 8), "total_latency_ms": round(_critical_path_latency(lat, edges), 3),
            "est_quality": round(quality, 6), "n_nodes": len(nodes), "per_node": per, "serves_truth": False}


def rank_candidates(candidate_dags: list, *, profile: PreferenceProfile | None = None, shard: str = "000") -> list:
    """Score many candidate DAGs by SIMULATED economics (per the user's profile) — beam-search ranking with NO execution.
    candidate_dags: [{nodes, edges}]. Returns [(index, estimate, score)] best (lowest score) first."""
    profile = profile or cost_first()
    if not candidate_dags:
        return []
    ests = [simulate_dag(c.get("nodes", []), c.get("edges"), shard=shard) for c in candidate_dags]
    routes = [{"resource_id": i, "deterministic": False,
               "economics": {"cost": e["total_cost"], "latency_ms": e["total_latency_ms"]}} for i, e in enumerate(ests)]
    scored = CM.score_routes(routes, profile)          # [(route, score)]
    order = sorted(range(len(ests)), key=lambda i: scored[i][1])
    return [(i, ests[i], round(scored[i][1], 6)) for i in order]
