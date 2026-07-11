"""economic_graph — the JOIN: model/component → providers → endpoints → LIVE economics, as one traversable graph.

Reads the config-tier economic registries (execution_backend_pricebook, inference_lane_profiles, model_provider_graph)
and OVERLAYS live observations (observation_store) so the router (System 22) traverses ONE economic graph rather than
querying siloed registries. A model's substitutable alternatives (CAN_REPLACE / CAN_FALLBACK_TO / SUPERSEDES edges) are
the secondary-provider routes that make arbitrage possible. serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from functools import lru_cache
from pathlib import Path

from src.teleon.economics import observation_store as OBS

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
_SUBSTITUTION_CODES = {1100, 1300, 1600}   # CAN_REPLACE / CAN_FALLBACK_TO / SUPERSEDES → a routing alternative


@lru_cache(maxsize=1)
def _pricebook() -> dict:
    return json.loads((_resource("architecture") / "execution_backend_pricebook.json").read_text()).get("backends", {})


@lru_cache(maxsize=1)
def _lanes() -> dict:
    return {ln["lane_id"]: ln for ln in
            json.loads((_resource("architecture") / "inference_lane_profiles.json").read_text())["lanes"]}


@lru_cache(maxsize=1)
def _graph() -> dict:
    return json.loads((_resource("architecture") / "model_provider_graph.json").read_text())


def _default_economics(resource_id: str) -> dict:
    """Config-tier default economics: from the lane profile, else the execution pricebook, else zeros (unknown)."""
    lane = _lanes().get(resource_id)
    if lane is not None:
        return {"cost": float(lane.get("cost", 0.0)), "latency_ms": float(lane.get("latency_ms", 0.0)),
                "is_local": bool(lane.get("is_local")), "source": "lane_profile"}
    pb = _pricebook().get(resource_id)
    if pb is not None:
        return {"cost": float(pb.get("request_cost", 0.0)), "latency_ms": None, "source": "pricebook"}
    return {"cost": 0.0, "latency_ms": None, "source": "unknown"}


def merged_economics(resource_id: str, *, shard: str = "000") -> dict:
    """Config default OVERLAID with live observations (live wins per field). The single economics view the cost model reads."""
    out = dict(_default_economics(resource_id))
    live = OBS.current_economics(resource_id, shard=shard)
    for f in ("cost", "latency_ms", "quality", "availability"):
        if live.get(f) is not None:
            out[f] = live[f]
    out["success_rate"] = live.get("success_rate")
    out["n_observations"] = live.get("n", 0)
    out["live"] = live.get("n", 0) > 0
    return out


def _provider_of(node_id: str) -> str:
    parts = node_id.split(".")            # e.g. "model.openai.frontier@candidate" -> "openai"
    return parts[1] if len(parts) >= 2 else node_id


def _route(resource_id: str, kind: str, *, display: str, external: bool, deterministic: bool, shard: str) -> dict:
    return {"resource_id": resource_id, "kind": kind, "provider": _provider_of(resource_id), "display": display,
            "external": external, "deterministic": deterministic, "economics": merged_economics(resource_id, shard=shard)}


def routes_for_model(model_node_id: str, *, shard: str = "000") -> list:
    """The model node + its substitutable alternatives, each a Route with merged economics. This is the arbitrage set:
    equivalent capability across providers — the router picks the cheapest viable one."""
    g = _graph()
    nodes = {n["node_id"]: n for n in g["nodes"]}
    ids = [model_node_id] if model_node_id in nodes else []
    for e in g.get("edges", []):
        if e.get("from") == model_node_id and e.get("edge_type_code") in _SUBSTITUTION_CODES and e.get("to") in nodes:
            ids.append(e["to"])
    seen, routes = set(), []
    for rid in ids:
        if rid in seen:
            continue
        seen.add(rid)
        n = nodes[rid]
        routes.append(_route(rid, "model", display=n.get("display", rid), external=bool(n.get("external")),
                             deterministic=n.get("adapter_style") == "deterministic_stub", shard=shard))
    return routes


def routes_for_lanes(*, capability_min: float | None = None, shard: str = "000") -> list:
    """Every inference lane as a route (optionally those clearing a capability floor) — the provider/endpoint market."""
    routes = []
    for lid, lane in _lanes().items():
        if capability_min is not None and float(lane.get("capability", 0.0)) < capability_min:
            continue
        routes.append(_route(lid, "lane", display=lane.get("display", lid), external=lane.get("egress") != "local",
                             deterministic=bool(lane.get("is_local")) and float(lane.get("capability", 1.0)) < 0.2,
                             shard=shard))
    return routes
