#!/usr/bin/env python3
"""Primitive provenance + self-aware optimization graph.

Owner directive 2026-07-01: store the relationships between the original primitives,
the search QUERY, the primitives FOUND, MUTATED, and ultimately USED, plus all logic /
transform / HISTORY, in a GRAPH — for analysis and self-aware optimization.

This is the memory substrate that makes the repair path-graph
(`_repos/shared-backend-components/scripts/primitive_repair_path_graph.py`) get SMARTER over time. It records an
append-only event history, derives a graph (nodes = query|primitive|mutation|route|
outcome; edges = found|mutated|uses|produced), and answers the optimization queries
that feed back into generation + repair + caching:

  - best_mutation_for_gap(gap)     -> which mutation fixes this gap-type most cheaply
                                      (re-orders the deterministic-first ladder)
  - proven_route_for_query(qkey)   -> caching/weighting: a similar query reuses a
                                      proven route instead of re-searching
  - gap_token_stats()              -> where tokens are actually spent (target for descent)
  - failure_hotspots()             -> negative memory: primitives/mutations that fail

Everything is candidate=true / serves_truth=false — evidence, not truth.

Usage:
  python3 _repos/shared-backend-components/scripts/primitive_provenance_graph.py --self-test
  python3 _repos/shared-backend-components/scripts/primitive_provenance_graph.py --report
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import collections
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import REPO_ROOT  # noqa: E402

LOG_PATH = _resource("data/dev-intel/primitive_provenance/events.jsonl")
OUT_DIR = _resource("data/dev-intel/primitive_provenance")

EVENT_TYPES = {
    "query_issued",       # {query_key, query_text, semantic_components}
    "primitive_found",    # {query_key, primitive_id, score}
    "primitive_mutated",  # {primitive_id, mutation, gap, result_primitive_id, tokens, deterministic}
    "route_composed",     # {route_id, query_key, primitive_ids, mutation_ids}
    "route_executed",     # {route_id, success, tokens, wall_ms, checkpoints_passed, checkpoints_failed}
}


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def query_key(text: str) -> str:
    """Semantic-ish cache handle: normalize + hash so near-identical queries collide
    (weighting reuses proven routes). Real system swaps this for an embedding LSH key."""
    norm = " ".join(sorted(text.lower().split()))
    return "q-" + hashlib.sha256(norm.encode()).hexdigest()[:16]


def record_event(event: dict[str, Any], *, log_path: Path = LOG_PATH) -> dict[str, Any]:
    assert event.get("type") in EVENT_TYPES, f"unknown event type: {event.get('type')}"
    event = {"event_id": "ev-" + hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()[:16],
             "ts": _now(), "candidate": True, "serves_truth": False, **event}
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def _read_events(log_path: Path) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    out = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def build_graph(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Derive nodes + typed edges from the event history."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    def node(nid: str, kind: str, **attrs: Any) -> None:
        if nid not in nodes:
            nodes[nid] = {"id": nid, "kind": kind, **attrs}
        else:
            nodes[nid].update(attrs)

    for e in events:
        t = e["type"]
        if t == "query_issued":
            node(e["query_key"], "query", text=e.get("query_text"),
                 semantic_components=e.get("semantic_components", []))
        elif t == "primitive_found":
            node(e["primitive_id"], "primitive")
            node(e["query_key"], "query")
            edges.append({"src": e["query_key"], "dst": e["primitive_id"], "rel": "found", "score": e.get("score")})
        elif t == "primitive_mutated":
            node(e["primitive_id"], "primitive")
            node(e["result_primitive_id"], "primitive")
            mid = f"mut:{e['mutation']}:{e.get('gap', '')}"
            node(mid, "mutation", mutation=e["mutation"], gap=e.get("gap"))
            edges.append({"src": e["primitive_id"], "dst": mid, "rel": "mutated_via",
                          "tokens": e.get("tokens", 0), "deterministic": e.get("deterministic", True)})
            edges.append({"src": mid, "dst": e["result_primitive_id"], "rel": "produced"})
        elif t == "route_composed":
            node(e["route_id"], "route")
            node(e["query_key"], "query")
            edges.append({"src": e["query_key"], "dst": e["route_id"], "rel": "answered_by"})
            for pid in e.get("primitive_ids", []):
                node(pid, "primitive")
                edges.append({"src": e["route_id"], "dst": pid, "rel": "uses"})
        elif t == "route_executed":
            node(e["route_id"], "route")
            edges.append({"src": e["route_id"], "dst": e["route_id"], "rel": "executed",
                          "success": e.get("success"), "tokens": e.get("tokens", 0)})
    return {"nodes": list(nodes.values()), "edges": edges,
            "node_count": len(nodes), "edge_count": len(edges)}


def best_mutation_for_gap(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Self-aware optimization: for each gap-type, the mutation with the best
    success/cost — this RE-ORDERS the deterministic-first ladder from real receipts."""
    # success per mutation comes from routes that used it and executed successfully.
    mut_ok: dict[tuple[str, str], int] = collections.Counter()
    mut_all: dict[tuple[str, str], int] = collections.Counter()
    mut_tokens: dict[tuple[str, str], list[int]] = collections.defaultdict(list)
    route_success: dict[str, bool] = {}
    route_mutations: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)

    for e in events:
        if e["type"] == "primitive_mutated":
            k = (e["mutation"], e.get("gap", ""))
            mut_all[k] += 1
            mut_tokens[k].append(e.get("tokens", 0))
        elif e["type"] == "route_executed":
            route_success[e["route_id"]] = bool(e.get("success"))
        elif e["type"] == "route_composed":
            for mid in e.get("mutation_ids", []):
                # mutation_ids encoded as "mutation|gap"
                if "|" in mid:
                    mm, gg = mid.split("|", 1)
                    route_mutations[e["route_id"]].append((mm, gg))
    for rid, muts in route_mutations.items():
        if route_success.get(rid):
            for k in muts:
                mut_ok[k] += 1
    out: dict[str, dict[str, Any]] = {}
    by_gap: dict[str, list[tuple[tuple[str, str], float, float]]] = collections.defaultdict(list)
    for k in mut_all:
        succ = mut_ok[k] / max(1, len([1 for rid, muts in route_mutations.items() if k in muts]))
        avg_tok = sum(mut_tokens[k]) / len(mut_tokens[k]) if mut_tokens[k] else 0
        by_gap[k[1]].append((k, succ, avg_tok))
    for gap, cands in by_gap.items():
        # prefer higher success, then lower tokens
        cands.sort(key=lambda x: (-x[1], x[2]))
        best = cands[0]
        out[gap] = {"mutation": best[0][0], "success_rate": round(best[1], 3), "avg_tokens": round(best[2], 1)}
    return out


def proven_route_for_query(events: list[dict[str, Any]], qkey: str) -> dict[str, Any] | None:
    """Caching/weighting: return the route that ANSWERED this query and EXECUTED
    successfully — so a similar query reuses it instead of re-searching."""
    route_for_q: dict[str, str] = {}
    route_success: dict[str, bool] = {}
    for e in events:
        if e["type"] == "route_composed":
            route_for_q[e["query_key"]] = e["route_id"]
        elif e["type"] == "route_executed":
            route_success[e["route_id"]] = bool(e.get("success"))
    rid = route_for_q.get(qkey)
    if rid and route_success.get(rid):
        return {"query_key": qkey, "proven_route_id": rid, "cache_hit": True}
    return None


def gap_token_stats(events: list[dict[str, Any]]) -> dict[str, Any]:
    tok: dict[str, list[int]] = collections.defaultdict(list)
    for e in events:
        if e["type"] == "primitive_mutated":
            tok[e.get("gap", "")].append(e.get("tokens", 0))
    return {g: {"n": len(v), "avg_tokens": round(sum(v) / len(v), 1), "total_tokens": sum(v)}
            for g, v in tok.items()}


def failure_hotspots(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fail: dict[str, int] = collections.Counter()
    total: dict[str, int] = collections.Counter()
    route_prims: dict[str, list[str]] = collections.defaultdict(list)
    for e in events:
        if e["type"] == "route_composed":
            for pid in e.get("primitive_ids", []):
                route_prims[e["route_id"]].append(pid)
        elif e["type"] == "route_executed":
            for pid in route_prims.get(e["route_id"], []):
                total[pid] += 1
                if not e.get("success"):
                    fail[pid] += 1
    out = [{"primitive_id": pid, "failures": fail[pid], "uses": total[pid],
            "failure_rate": round(fail[pid] / total[pid], 3)} for pid in total if fail[pid]]
    out.sort(key=lambda x: -x["failure_rate"])
    return out


def build_report(events: list[dict[str, Any]]) -> dict[str, Any]:
    graph = build_graph(events)
    return {
        "record_type": "primitive_provenance_optimization_report",
        "generated_utc": dt.datetime.now(dt.timezone.utc).date().isoformat(),
        "event_count": len(events),
        "graph": {"node_count": graph["node_count"], "edge_count": graph["edge_count"]},
        "best_mutation_for_gap": best_mutation_for_gap(events),
        "gap_token_stats": gap_token_stats(events),
        "failure_hotspots": failure_hotspots(events),
        "candidate": True, "serves_truth": False,
    }


def _synthetic_events() -> list[dict[str, Any]]:
    qk = query_key("import customer csv and sync to crm")
    return [
        {"type": "query_issued", "query_key": qk, "query_text": "import customer csv and sync to crm",
         "semantic_components": ["csv_parse", "dedupe", "crm_upsert"]},
        {"type": "primitive_found", "query_key": qk, "primitive_id": "prim:csv_parse", "score": 0.9},
        {"type": "primitive_found", "query_key": qk, "primitive_id": "prim:crm_upsert_scalar", "score": 0.7},
        {"type": "primitive_mutated", "primitive_id": "prim:crm_upsert_scalar", "mutation": "scalar_to_array",
         "gap": "scalar->array", "result_primitive_id": "prim:crm_upsert_batch", "tokens": 0, "deterministic": True},
        {"type": "route_composed", "route_id": "route:csv_crm_1", "query_key": qk,
         "primitive_ids": ["prim:csv_parse", "prim:crm_upsert_batch"], "mutation_ids": ["scalar_to_array|scalar->array"]},
        {"type": "route_executed", "route_id": "route:csv_crm_1", "success": True, "tokens": 0,
         "wall_ms": 120, "checkpoints_passed": 4, "checkpoints_failed": 0},
        # a failing route to exercise negative memory + hotspots
        {"type": "primitive_found", "query_key": qk, "primitive_id": "prim:crm_upsert_hosted", "score": 0.6},
        {"type": "route_composed", "route_id": "route:csv_crm_2", "query_key": qk,
         "primitive_ids": ["prim:csv_parse", "prim:crm_upsert_hosted"], "mutation_ids": []},
        {"type": "route_executed", "route_id": "route:csv_crm_2", "success": False, "tokens": 1500,
         "wall_ms": 900, "checkpoints_passed": 2, "checkpoints_failed": 1},
    ]


def self_test() -> int:
    ev = _synthetic_events()
    # query_key is stable + collides on reordered/case-different text.
    assert query_key("Import CSV") == query_key("csv import")
    # graph derivation links query->found->mutated->produced->route->uses.
    g = build_graph(ev)
    assert g["node_count"] > 0 and g["edge_count"] > 0
    rels = {e["rel"] for e in g["edges"]}
    assert {"found", "mutated_via", "produced", "uses", "answered_by", "executed"} <= rels, rels
    # best mutation for the scalar->array gap is the deterministic scalar_to_array at 0 tokens.
    best = best_mutation_for_gap(ev)
    assert "scalar->array" in best
    assert best["scalar->array"]["mutation"] == "scalar_to_array"
    assert best["scalar->array"]["avg_tokens"] == 0
    # caching: the proven route is the SUCCESSFUL one, not the failed one.
    qk = query_key("import customer csv and sync to crm")
    proven = proven_route_for_query(ev, qk)
    assert proven and proven["proven_route_id"] == "route:csv_crm_1"
    # token stats attribute spend to the gap.
    stats = gap_token_stats(ev)
    assert stats["scalar->array"]["avg_tokens"] == 0
    # failure hotspots surface the hosted upsert primitive (negative memory).
    hot = failure_hotspots(ev)
    assert any(h["primitive_id"] == "prim:crm_upsert_hosted" and h["failures"] >= 1 for h in hot)
    # report renders.
    rep = build_report(ev)
    assert rep["event_count"] == len(ev) and rep["best_mutation_for_gap"]
    print("OK: provenance graph self-test passed (event->graph, best-mutation-per-gap, "
          "query->proven-route cache, gap token stats, failure hotspots).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args(argv)
    if args.report:
        events = _read_events(LOG_PATH) or _synthetic_events()
        rep = build_report(events)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "optimization_report.json").write_text(json.dumps(rep, indent=2) + "\n")
        print(f"wrote {OUT_DIR}/optimization_report.json — {rep['event_count']} events, "
              f"{rep['graph']['node_count']} nodes, {rep['graph']['edge_count']} edges")
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
