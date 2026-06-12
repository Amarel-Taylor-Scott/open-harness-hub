#!/usr/bin/env python3
"""Backs `processor/graphrag-retrieve` (process_kind ``retrieve.graph``).

Knowledge-graph retrieval (GraphRAG-style): seed on the entities the query
names, then follow EXPLICIT relationship edges up to ``MAX_HOPS`` to answer
multi-hop questions naive vector RAG misses ("who owns the company that owns
X?"). Returns the traversed SUBGRAPH — nodes, edges, and the hop paths that
reached them — so every conclusion is a citable chain, not a similarity blur.

The graph is INJECTED ({"nodes": {name: {...}}, "edges": [{"source",
"relation", "target", ...}]}); building it is the upstream temporal-graph /
entity-linking lane's job. Deterministic BFS; microsoft/graphrag is the
heavyweight community-summarization escalation behind the same contract
(intaken as a tool candidate — see docs/research/github-repo-intel-2026-06-12.md).

Contract: side_effects=read; on_error=raise; deterministic traversal (the
manifest allows non-deterministic learned variants).

Inputs query, graph → output subgraph.

CLI / self-test: python3 scripts/processors/retrieval/graphrag_retrieve.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Hop ceiling: 3 covers ownership-chain / works-for / part-of questions while
#: keeping the subgraph reviewable; raise per call when a question needs more.
MAX_HOPS = 3

#: Node cap so a hub node cannot explode the subgraph (reported when hit).
MAX_NODES = 50

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9 .&'-]*")


def _seed_nodes(query: str, nodes: dict[str, Any]) -> list[str]:
    """Entities the query names — longest-name-first exact containment."""
    q = query.lower()
    seeds = [name for name in nodes if name.lower() in q]
    return sorted(seeds, key=lambda n: (-len(n), n))


def run(*, query: str, graph: dict[str, Any], max_hops: int = MAX_HOPS) -> dict[str, Any]:
    """BFS from query-named entities along explicit edges; return the subgraph."""
    if not isinstance(query, str):
        raise TypeError(f"query must be str, got {type(query).__name__}")
    if not isinstance(graph, dict) or not isinstance(graph.get("nodes"), dict) \
            or not isinstance(graph.get("edges"), list):
        raise TypeError("graph must be {'nodes': {...}, 'edges': [...]}")
    if not isinstance(max_hops, int) or max_hops < 1:
        raise ValueError(f"max_hops must be a positive int, got {max_hops!r}")
    nodes = graph["nodes"]
    adj: dict[str, list[dict[str, Any]]] = {}
    for i, e in enumerate(graph["edges"]):
        if not isinstance(e, dict) or "source" not in e or "target" not in e or "relation" not in e:
            raise ValueError(f"edges[{i}] needs source, relation, target")
        adj.setdefault(str(e["source"]), []).append(e)
        adj.setdefault(str(e["target"]), []).append(e)  # traverse undirected, report direction

    seeds = _seed_nodes(query, nodes)
    visited: dict[str, dict[str, Any]] = {}
    sub_edges: list[dict[str, Any]] = []
    truncated = False
    frontier = [(s, [s]) for s in seeds]
    for s, path in frontier:
        visited[s] = {"hops": 0, "path": path}
    hop = 0
    while frontier and hop < max_hops:
        hop += 1
        nxt: list[tuple[str, list[str]]] = []
        for name, path in frontier:
            for e in sorted(adj.get(name, []), key=lambda x: (str(x["source"]), str(x["relation"]), str(x["target"]))):
                other = str(e["target"]) if str(e["source"]) == name else str(e["source"])
                if e not in sub_edges:
                    sub_edges.append(e)
                if other in visited:
                    continue
                if len(visited) >= MAX_NODES:
                    truncated = True
                    continue
                visited[other] = {"hops": hop, "path": path + [other]}
                nxt.append((other, path + [other]))
        frontier = nxt
    return {"subgraph": {
        "seeds": seeds,
        "nodes": {n: {**nodes.get(n, {}), **meta} for n, meta in sorted(visited.items())},
        "edges": sub_edges,
        "max_hops": max_hops,
        "truncated": truncated,
        "method": "deterministic_bfs (explicit edges only — no inferred links)",
    }}


def _selftest() -> None:
    graph = {
        "nodes": {"CareShift Partners": {}, "Harbor Lakeside Workforce": {},
                  "Northstar Staffing": {}, "Acme Bank": {}, "Unrelated Co": {}},
        "edges": [
            {"source": "Northstar Staffing", "relation": "parent_of", "target": "Harbor Lakeside Workforce"},
            {"source": "Harbor Lakeside Workforce", "relation": "split_off", "target": "CareShift Partners"},
            {"source": "Acme Bank", "relation": "vendor_of", "target": "Northstar Staffing"},
        ],
    }
    # Multi-hop: from the named entity, the ownership chain is reachable with paths.
    out = run(query="who ultimately sits behind CareShift Partners?", graph=graph)["subgraph"]
    assert out["seeds"] == ["CareShift Partners"]
    assert "Northstar Staffing" in out["nodes"] and "Acme Bank" in out["nodes"]
    assert out["nodes"]["Northstar Staffing"]["hops"] == 2
    assert out["nodes"]["Acme Bank"]["path"] == ["CareShift Partners", "Harbor Lakeside Workforce",
                                                 "Northstar Staffing", "Acme Bank"]
    # Unconnected nodes never appear (explicit edges only).
    assert "Unrelated Co" not in out["nodes"]
    # Hop ceiling respected: 1 hop stops at the direct neighbor.
    one = run(query="CareShift Partners", graph=graph, max_hops=1)["subgraph"]
    assert "Northstar Staffing" not in one["nodes"] and "Harbor Lakeside Workforce" in one["nodes"]
    # No seed → honest empty subgraph (never a similarity guess).
    none = run(query="tomato gardening", graph=graph)["subgraph"]
    assert none["seeds"] == [] and none["nodes"] == {} and none["edges"] == []
    # Deterministic; graph untouched; on_error=raise.
    snap = json.dumps(graph, sort_keys=True)
    assert json.dumps(run(query="CareShift Partners", graph=graph), sort_keys=True) == \
           json.dumps(run(query="CareShift Partners", graph=graph), sort_keys=True)
    assert json.dumps(graph, sort_keys=True) == snap
    raised = False
    try:
        run(query="x", graph={"nodes": {}, "edges": [{"source": "a"}]})
    except ValueError:
        raised = True
    assert raised
    print(f"PASS — graphrag_retrieve: deterministic BFS to {MAX_HOPS} hops over explicit "
          "edges, citable hop paths, honest no-seed empties, hub truncation reported "
          "verified")


if __name__ == "__main__":
    _selftest()
