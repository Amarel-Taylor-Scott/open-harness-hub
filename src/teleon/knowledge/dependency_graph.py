"""knowledge.dependency_graph — Dependency Graph Intelligence (the owner's Registry #92 / §3).

Most repos are not isolated — everything depends on something. This builds a directed dependency graph from declared
'package -> requires' edges (seeded from architecture/package_dependency_seed.json; full graph scraped from PyPI/npm
manifests via #91) and answers the reinvention question at the STACK level: 'why build a custom PDF parser — this
whole dependency stack (ocrmypdf -> pikepdf/pdfminer/pillow/tesseract) already provides it?'

Deterministic (no model): transitive closure, cycle detection, ecosystem clusters (connected components), and
capability coverage ('which existing package, with its transitive deps, already provides these capabilities?').
serves_truth=false; a match is a governed CANDIDATE ('this stack likely covers it — verify'), never an assertion.
"""
from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "architecture" / "package_dependency_seed.json"


def load_packages() -> list[dict]:
    return json.loads(_SEED.read_text())["packages"]


def build_graph(packages: list[dict] | None = None) -> dict:
    """Directed graph: {nodes: {id: record}, edges: {id: [requires...]}, provides: {capability: [ids]}}."""
    pkgs = packages if packages is not None else load_packages()
    nodes = {p["id"]: p for p in pkgs}
    edges = {p["id"]: list(p.get("requires", [])) for p in pkgs}
    provides: dict[str, list[str]] = {}
    for p in pkgs:
        for cap in p.get("provides", []):
            provides.setdefault(cap, []).append(p["id"])
    return {"nodes": nodes, "edges": edges, "provides": provides}


def transitive_deps(graph: dict, node: str) -> list[str]:
    """All packages reachable from `node` (its full dependency closure), excluding `node`. Cycle-safe."""
    seen: set[str] = set()
    stack = list(graph["edges"].get(node, []))
    while stack:
        d = stack.pop()
        if d in seen:
            continue
        seen.add(d)
        stack.extend(graph["edges"].get(d, []))
    seen.discard(node)
    return sorted(seen)


def detect_cycle(graph: dict) -> list[str]:
    """Return one cycle (node ids) if the dependency graph has one, else []."""
    WHITE, GREY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph["edges"]}
    path: list[str] = []

    def visit(n: str) -> list[str]:
        if n not in color:  # external dep not in our node set
            return []
        color[n] = GREY
        path.append(n)
        for d in graph["edges"].get(n, []):
            if color.get(d) == GREY:
                return path[path.index(d):] + [d]
            if color.get(d, BLACK) == WHITE:
                c = visit(d)
                if c:
                    return c
        path.pop()
        color[n] = BLACK
        return []

    for n in list(graph["edges"]):
        if color[n] == WHITE:
            c = visit(n)
            if c:
                return c
    return []


def ecosystem_cluster(graph: dict, node: str) -> list[str]:
    """The connected component (undirected) around `node` — its ecosystem cluster."""
    adj: dict[str, set[str]] = {}
    for src, deps in graph["edges"].items():
        for d in deps:
            adj.setdefault(src, set()).add(d)
            adj.setdefault(d, set()).add(src)
    seen = {node}
    stack = [node]
    while stack:
        n = stack.pop()
        for m in adj.get(n, ()):
            if m not in seen:
                seen.add(m)
                stack.append(m)
    return sorted(seen)


def stack_exists(capabilities: list[str], graph: dict | None = None) -> dict:
    """Does an existing package (with its transitive deps) already cover ALL requested capabilities? The stack-level
    reinvention check. Returns the covering packages + a governed candidate verdict."""
    g = graph if graph is not None else build_graph()
    wanted = set(capabilities)
    covering = []
    for nid, rec in g["nodes"].items():
        covered = set(rec.get("provides", []))
        for dep in transitive_deps(g, nid):
            covered |= set(g["nodes"].get(dep, {}).get("provides", []))
        if wanted <= covered:
            covering.append({"package": nid, "transitive_deps": transitive_deps(g, nid),
                             "provides": sorted(covered & wanted)})
    return {
        "capabilities": sorted(wanted),
        "stack_exists": bool(covering),
        "covering_packages": covering,
        "verdict": ("a dependency stack already provides this — don't rebuild it (verify fit)" if covering
                    else "no single existing stack covers all of these — may be genuinely novel"),
        "serves_truth": False, "candidate": True,
    }


def _self_test() -> list[str]:
    fails = []

    def ck(name, ok):
        if not ok:
            fails.append(f"dependency_graph: {name}")
            print(f"  [XX] dependency_graph: {name}")

    g = build_graph()
    ck("graph has nodes + edges + provides", g["nodes"] and g["edges"] and g["provides"])
    ck("transitive closure reaches indirect deps", "lxml" in transitive_deps(g, "ocrmypdf"))
    ck("transitive closure excludes self", "ocrmypdf" not in transitive_deps(g, "ocrmypdf"))
    ck("no false cycle in an acyclic seed", detect_cycle(g) == [])
    # inject a cycle -> detected
    cyc = build_graph([{"id": "a", "requires": ["b"], "provides": []},
                       {"id": "b", "requires": ["a"], "provides": []}])
    ck("detects an injected cycle", len(detect_cycle(cyc)) >= 2)
    ck("ecosystem cluster groups the pdf stack", "pdfminer-six" in ecosystem_cluster(g, "ocrmypdf"))
    se = stack_exists(["ocr", "pdf_text_extraction"], g)
    ck("stack_exists finds the ocr+pdf stack (ocrmypdf)", se["stack_exists"] and any(
        c["package"] == "ocrmypdf" for c in se["covering_packages"]))
    ck("stack_exists honest on a novel combo", not stack_exists(["time_travel", "telepathy"], g)["stack_exists"])
    ck("verdict is a governed candidate", se["serves_truth"] is False and se["candidate"])
    return fails
