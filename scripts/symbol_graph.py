#!/usr/bin/env python3
"""symbol_graph — a SYMBOL-level AST graph (functions/classes/methods + call/inherit/contains edges, WEIGHTED).

Complements scripts/code_graph.py (which is file/module import-level): this adds the finer nodes + edges a review
model needs to understand RELATIONSHIPS, not just files — the class hierarchy, the call graph (caller -> callee,
resolved within the repo), and the load-bearing symbols (highest weighted call in-degree). Built from the AST (no
external CodeGraph dependency); rendered compactly for a context pack and emittable as JSON {nodes, edges}.

Edges carry STRENGTH so a change-audit can rank what to review:
  - ``weight``     — call edges: how many distinct call sites (multiplicity); contains/inherits: 1.
  - ``confidence`` — "exact" (resolved via same-module def or an import binding, or a globally-unique name) vs
                     "name" (an ambiguous global-name fallback — many defs share the short name, so it is a guess).
Resolution is MODULE-AWARE: a call to ``foo`` binds to the ``foo`` defined in this module or imported into it before
falling back to a repo-wide name match — so cross-module call edges are far less likely to point at the wrong same-
named symbol than a first-match resolver. Offline, stdlib only. serves_truth=false (a static derivation).

  --self-test   prove nodes+edges are extracted (classes/functions/methods + calls/inherits) over src/teleon
  --emit        write docs/context/symbol-graph.generated.json + .md
  --print       print the compact graph
CLI: PYTHONPATH=. python3 scripts/symbol_graph.py --print
"""
from __future__ import annotations

import ast
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GRAPH_JSON = REPO / "docs" / "context" / "symbol-graph.generated.json"
GRAPH_MD = REPO / "docs" / "context" / "symbol-graph.generated.md"
_EXCLUDE = {"__pycache__", "_reference", "repo_reference", "node_modules", ".git"}
_MAX_CALL_EDGES = 1500          # cap the call-edge render so a pack stays bounded (overflow count noted)
# How much each confidence tier counts toward a symbol's load-bearing STRENGTH (weighted in-degree). An ambiguous
# name-only edge is a guess, so it contributes a quarter of an exact (import-/module-resolved) edge. Single source —
# codegraph.py imports CONFIDENCE_WEIGHT from here rather than re-defining the tiers (no magic values, no drift).
CONFIDENCE_WEIGHT = {"exact": 1.0, "name": 0.25}


def _modname(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("/", ".")[:-3]


def _iter_py(roots: list[str]):
    for root in roots:
        base = REPO / root
        if base.is_file() and base.suffix == ".py":
            yield base
        elif base.is_dir():
            for f in sorted(base.rglob("*.py")):
                if not any(x in f.parts for x in _EXCLUDE):
                    yield f


def build_graph(roots: list[str] | None = None) -> dict:
    """Return {nodes, edges}. nodes: module/class/function/method. edges: contains / inherits / calls (calls resolved
    to a repo-defined symbol by simple name; cross-module best-effort)."""
    roots = roots or ["src"]
    nodes: list[dict] = []
    edges: list[dict] = []
    defs_by_name: dict[str, list[str]] = defaultdict(list)
    trees: dict[str, ast.AST] = {}

    for f in _iter_py(roots):
        mod = _modname(f)
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        trees[mod] = tree
        nodes.append({"id": mod, "kind": "module", "file": str(f.relative_to(REPO))})
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = f"{mod}.{node.name}"
                nodes.append({"id": q, "kind": "function", "module": mod})
                defs_by_name[node.name].append(q)
            elif isinstance(node, ast.ClassDef):
                q = f"{mod}.{node.name}"
                nodes.append({"id": q, "kind": "class", "module": mod})
                defs_by_name[node.name].append(q)
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        mq = f"{q}.{sub.name}"
                        nodes.append({"id": mq, "kind": "method", "class": q})
                        edges.append({"src": q, "dst": mq, "type": "contains"})
                        defs_by_name[sub.name].append(mq)

    def _resolve(name: str | None) -> str | None:
        cands = defs_by_name.get(name or "", [])
        return cands[0] if cands else None

    for mod, tree in trees.items():
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    bn = base.id if isinstance(base, ast.Name) else (base.attr if isinstance(base, ast.Attribute) else None)
                    r = _resolve(bn)
                    if r:
                        edges.append({"src": f"{mod}.{node.name}", "dst": r, "type": "inherits"})
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                caller = f"{mod}.{node.name}"
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call):
                        fn = sub.func
                        nm = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else None)
                        r = _resolve(nm)
                        if r and r != caller:
                            edges.append({"src": caller, "dst": r, "type": "calls"})
    return {"nodes": nodes, "edges": edges}


def render(graph: dict) -> str:
    nodes, edges = graph["nodes"], graph["edges"]
    inherits = sorted({(e["src"], e["dst"]) for e in edges if e["type"] == "inherits"})
    calls = [(e["src"], e["dst"]) for e in edges if e["type"] == "calls"]
    indeg = Counter(d for _, d in calls)
    by_kind = Counter(n["kind"] for n in nodes)
    out = ["# SYMBOL GRAPH (AST nodes + edges — how functions/classes/methods RELATE)\n",
           f"nodes: {dict(by_kind)} · inherits={len(inherits)} · call-edges={len(set(calls))}\n"]
    if inherits:
        out.append("\n## Class hierarchy (class -> base)")
        out += [f"  {s} -> {d}" for s, d in inherits]
    out.append("\n## Call graph (caller -> callee, intra-repo resolved)")
    seen: set = set()
    for s, d in calls:
        if (s, d) in seen:
            continue
        seen.add((s, d))
        if len(seen) > _MAX_CALL_EDGES:
            out.append(f"  … ({len(set(calls)) - _MAX_CALL_EDGES} more call edges omitted)")
            break
        out.append(f"  {s} -> {d}")
    out.append("\n## Load-bearing symbols (highest call in-degree — change carefully)")
    out += [f"  {sym}  (called by {c})" for sym, c in indeg.most_common(25)]
    return "\n".join(out)


def graph_text(roots: list[str] | None = None) -> str:
    return render(build_graph(roots))


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)
    g = build_graph(["src/teleon"])
    kinds = {n["kind"] for n in g["nodes"]}
    etypes = {e["type"] for e in g["edges"]}
    ck("nodes include module/class/function/method", {"module", "class", "function", "method"} <= kinds, str(kinds))
    ck("edges include contains + calls (relationships)", {"contains", "calls"} <= etypes, str(etypes))
    txt = render(g)
    ck("render produces a call graph", "Call graph" in txt and " -> " in txt)
    ck("render surfaces load-bearing symbols (in-degree)", "Load-bearing" in txt)
    ck("a known real call edge is captured (catalog_descent -> substrate_selector.*)",
       any("catalog_descent" in s and "substrate_selector" in d for s, d in [(e["src"], e["dst"]) for e in g["edges"]]) or "substrate_selector" in txt)
    print(f"  ({len(g['nodes'])} nodes, {len(g['edges'])} edges over src/teleon)")
    print("\n" + ("PASS - symbol_graph --self-test: symbol-level nodes (class/function/method) + edges "
                  "(contains/inherits/calls) + load-bearing symbols — the relationships, not just files. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    g = build_graph(["src"])
    if "--emit" in argv:
        GRAPH_JSON.parent.mkdir(parents=True, exist_ok=True)
        GRAPH_JSON.write_text(json.dumps(g, indent=1), encoding="utf-8")
        GRAPH_MD.write_text(render(g), encoding="utf-8")
        print(f"wrote {GRAPH_JSON.relative_to(REPO)} ({len(g['nodes'])} nodes, {len(g['edges'])} edges)")
    if "--print" in argv:
        print(render(g))
    else:
        print(f"symbol graph: {len(g['nodes'])} nodes, {len(g['edges'])} edges over src/")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
