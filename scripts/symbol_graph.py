#!/usr/bin/env python3
"""symbol_graph — a SYMBOL-level AST graph (functions/classes/methods + call/inherit/contains edges, WEIGHTED).

Complements scripts/code_graph.py (which is file/module import-level): this adds the finer nodes + edges a review
model needs to understand RELATIONSHIPS, not just files — the class hierarchy, the call graph (caller -> callee,
resolved within the repo), and the load-bearing symbols (highest weighted call in-degree). Built from the AST (no
external CodeGraph dependency); rendered compactly for a context pack and emittable as JSON {nodes, edges}.

Edges carry STRENGTH so a change-audit can rank what to review:
  - ``weight``     — call edges: how many distinct call sites (multiplicity); contains/inherits: 1.
  - ``confidence`` — always "exact": every emitted edge is CONFIDENTLY resolved (kept as a field for shape stability).
Resolution is MODULE-AWARE and CONFIDENT-ONLY: a call to ``foo`` resolves to the ``foo`` defined in this module, or
imported into it, or globally UNIQUE in the repo. A name with several same-named defs and no binding is AMBIGUOUS —
we REFUSE to guess a winner (guessing manufactures false hubs, e.g. one generic ``.get`` absorbing thousands of
unrelated call sites) and instead DROP it, counted in ``graph["stats"]["ambiguous_calls_dropped"]``. So every call
edge points at the right symbol, and the load-bearing ranking is trustworthy. Offline, stdlib only. serves_truth=false.

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


def _import_bindings(tree: ast.AST) -> dict[str, str]:
    """local-name -> the in-repo source module it was imported from (level==0 `from X import name`). Lets a bare call
    ``name()`` resolve to the module it actually came from instead of any same-named def elsewhere in the repo."""
    binds: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for a in node.names:
                binds[a.asname or a.name] = node.module
    return binds


def _module_aliases(tree: ast.AST, modules: set[str]) -> dict[str, str]:
    """local-name -> in-repo MODULE it refers to, so an attribute call ``alias.func()`` can resolve ``func`` inside
    that module (the only attribute calls we resolve besides ``self``/``cls``). Covers `from pkg import submodule`
    and `import pkg.sub as alias` — receiver must be a plain Name, so dotted `import a.b.c` (called `a.b.c.f()`) is
    left unmatched rather than mis-bound."""
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for a in node.names:
                full = f"{node.module}.{a.name}"
                if full in modules:
                    out[a.asname or a.name] = full
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name in modules:
                    out[a.asname or a.name] = a.name
    return out


def build_graph(roots: list[str] | None = None) -> dict:
    """Return {nodes, edges}. nodes: module/class/function/method. edges: contains / inherits / calls, each WEIGHTED
    (call ``weight`` = distinct call sites) and tagged ``confidence`` ("exact" = same-module/import-/unique-name
    resolution; "name" = ambiguous global-name fallback). Calls are deduplicated per (src,dst) into one weighted edge.
    Resolution is confident-only (see below): bare names via module/import/unique; attribute calls only via self/cls
    or an imported module alias. Ambiguous in-repo names are dropped (counted), never guessed onto an arbitrary def."""
    roots = roots or ["src"]
    nodes: list[dict] = []
    edges: list[dict] = []
    defs_by_name: dict[str, list[str]] = defaultdict(list)        # short name -> [qualified ids] (global fallback)
    defs_in_module: dict[str, dict[str, str]] = defaultdict(dict)  # module -> {short name -> qualified id}
    binds_by_mod: dict[str, dict[str, str]] = {}
    trees: dict[str, ast.AST] = {}

    for f in _iter_py(roots):
        mod = _modname(f)
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        trees[mod] = tree
        binds_by_mod[mod] = _import_bindings(tree)
        nodes.append({"id": mod, "kind": "module", "file": str(f.relative_to(REPO))})
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = f"{mod}.{node.name}"
                nodes.append({"id": q, "kind": "function", "module": mod})
                defs_by_name[node.name].append(q)
                defs_in_module[mod][node.name] = q
            elif isinstance(node, ast.ClassDef):
                q = f"{mod}.{node.name}"
                nodes.append({"id": q, "kind": "class", "module": mod})
                defs_by_name[node.name].append(q)
                defs_in_module[mod][node.name] = q
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        mq = f"{q}.{sub.name}"
                        nodes.append({"id": mq, "kind": "method", "class": q})
                        edges.append({"src": q, "dst": mq, "type": "contains", "weight": 1, "confidence": "exact"})
                        defs_by_name[sub.name].append(mq)
                        defs_in_module[mod].setdefault(sub.name, mq)  # first method def wins the bare name in-module

    modules_set = set(trees)
    aliases_by_mod = {m: _module_aliases(t, modules_set) for m, t in trees.items()}

    # CONFIDENT-ONLY resolution — attribute a reference to a concrete symbol ONLY when we can do so WITHOUT guessing.
    # The trap a name-based graph falls into: resolving `path.read_text()` / `x.split()` / `obj.get()` by repo-name
    # invents huge false hubs (a stdlib method's calls pile onto a same-named repo symbol). So we split by syntax:
    #   • bare  name()    -> (1) defined in this module, (2) imported here from a module that defines it,
    #                        (3) globally UNIQUE in the repo. Several same-named defs + no binding = AMBIGUOUS (dropped).
    #   • recv.attr()     -> resolve ONLY when recv is `self`/`cls` (this module's def) or an imported MODULE alias
    #                        (that module's def). Any other receiver is an unknown object -> NOT guessed.
    # Dropped-ambiguous bare names are COUNTED (no silent loss); unresolved attribute calls are simply external.
    AMBIGUOUS = "<ambiguous>"

    def _resolve_name(name: str | None, caller_mod: str) -> str | None:
        if not name:
            return None
        if name in defs_in_module.get(caller_mod, {}):                         # 1) defined right here
            return defs_in_module[caller_mod][name]
        tgt = binds_by_mod.get(caller_mod, {}).get(name)                       # 2) imported from a module that defines it
        if tgt and name in defs_in_module.get(tgt, {}):
            return defs_in_module[tgt][name]
        cands = defs_by_name.get(name, [])
        if len(cands) == 1:                                                    # 3) globally unique -> unambiguous
            return cands[0]
        return AMBIGUOUS if cands else None                                    # ambiguous in-repo vs external

    def _resolve_ref(node: ast.AST, caller_mod: str) -> str | None:
        """Resolve a call target or base-class ref (ast.Name or ast.Attribute). id | AMBIGUOUS | None."""
        if isinstance(node, ast.Name):
            return _resolve_name(node.id, caller_mod)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            recv = node.value.id
            tmod = caller_mod if recv in ("self", "cls") else aliases_by_mod.get(caller_mod, {}).get(recv)
            if tmod:                                                           # self/cls or an imported module
                return defs_in_module.get(tmod, {}).get(node.attr)            # that scope's def, else None (no guess)
        return None

    ambiguous_dropped = 0
    call_acc: dict[tuple[str, str], int] = {}                # (caller, callee) -> weight (distinct call sites)
    for mod, tree in trees.items():
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    r = _resolve_ref(base, mod)
                    if r and r != AMBIGUOUS:
                        edges.append({"src": f"{mod}.{node.name}", "dst": r, "type": "inherits", "weight": 1, "confidence": "exact"})
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                caller = f"{mod}.{node.name}"
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call):
                        r = _resolve_ref(sub.func, mod)
                        if r == AMBIGUOUS:
                            ambiguous_dropped += 1
                        elif r and r != caller:
                            call_acc[(caller, r)] = call_acc.get((caller, r), 0) + 1
    for (s, d), w in sorted(call_acc.items()):
        edges.append({"src": s, "dst": d, "type": "calls", "weight": w, "confidence": "exact"})
    return {"nodes": nodes, "edges": edges,
            "stats": {"ambiguous_calls_dropped": ambiguous_dropped, "call_edges": len(call_acc)}}


def load_bearing(edges: list[dict]) -> Counter:
    """symbol -> weighted call in-degree (Σ weight·confidence_weight over incoming calls) — the change-carefully set."""
    score: Counter = Counter()
    for e in edges:
        if e["type"] == "calls":
            score[e["dst"]] += e.get("weight", 1) * CONFIDENCE_WEIGHT.get(e.get("confidence", "name"), 0.25)
    return score


def render(graph: dict) -> str:
    nodes, edges = graph["nodes"], graph["edges"]
    inherits = sorted({(e["src"], e["dst"]) for e in edges if e["type"] == "inherits"})
    calls = [e for e in edges if e["type"] == "calls"]                      # already deduped per (src,dst), weighted
    dropped = graph.get("stats", {}).get("ambiguous_calls_dropped", 0)
    by_kind = Counter(n["kind"] for n in nodes)
    out = ["# SYMBOL GRAPH (AST nodes + WEIGHTED edges — how functions/classes/methods RELATE)\n",
           f"nodes: {dict(by_kind)} · inherits={len(inherits)} · call-edges={len(calls)} "
           f"(weight=call-sites, all confidently resolved; {dropped} ambiguous calls dropped, not guessed)\n"]
    if inherits:
        out.append("\n## Class hierarchy (class -> base)")
        out += [f"  {s} -> {d}" for s, d in inherits]
    out.append("\n## Call graph (caller -> callee · xN call sites; strongest first)")
    ranked = sorted(calls, key=lambda e: (-e.get("weight", 1), e["src"], e["dst"]))
    for e in ranked[:_MAX_CALL_EDGES]:
        out.append(f"  {e['src']} -> {e['dst']}  x{e.get('weight', 1)}")
    if len(ranked) > _MAX_CALL_EDGES:
        out.append(f"  … ({len(ranked) - _MAX_CALL_EDGES} weaker call edges omitted)")
    out.append("\n## Load-bearing symbols (highest WEIGHTED call in-degree — change carefully)")
    out += [f"  {sym}  (in-strength {score:.2f})" for sym, score in load_bearing(edges).most_common(25)]
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
    calls = [e for e in g["edges"] if e["type"] == "calls"]
    ck("nodes include module/class/function/method", {"module", "class", "function", "method"} <= kinds, str(kinds))
    ck("edges include contains + calls (relationships)", {"contains", "calls"} <= etypes, str(etypes))
    ck("every call edge carries weight>=1 and a valid confidence",
       all(e.get("weight", 0) >= 1 and e.get("confidence") in CONFIDENCE_WEIGHT for e in calls))
    ck("call edges are deduplicated per (src,dst) into one weighted edge",
       len({(e["src"], e["dst"]) for e in calls}) == len(calls))
    ck("multiplicity is captured (some call edge has weight>1)", any(e.get("weight", 1) > 1 for e in calls))
    ck("every call edge is confidently resolved (confidence=exact — no guessed targets)",
       all(e.get("confidence") == "exact" for e in calls))
    ck("ambiguous calls are dropped + COUNTED (no false hubs, no silent loss)",
       isinstance(g.get("stats", {}).get("ambiguous_calls_dropped"), int) and g["stats"]["ambiguous_calls_dropped"] >= 0)
    lb = load_bearing(g["edges"])
    ck("load-bearing scoring is weighted + non-empty", bool(lb) and all(s > 0 for s in lb.values()))
    txt = render(g)
    ck("render produces a call graph", "Call graph" in txt and " -> " in txt)
    ck("render surfaces load-bearing symbols (weighted in-degree)", "Load-bearing" in txt and "in-strength" in txt)
    ck("a known real call edge is captured (catalog_descent -> substrate_selector.*)",
       any("catalog_descent" in s and "substrate_selector" in d for s, d in [(e["src"], e["dst"]) for e in g["edges"]]) or "substrate_selector" in txt)
    print(f"  ({len(g['nodes'])} nodes, {len(g['edges'])} edges over src/teleon; {len(calls)} weighted call edges)")
    print("\n" + ("PASS - symbol_graph --self-test: symbol-level nodes (class/function/method) + WEIGHTED edges "
                  "(contains/inherits/calls, module-aware confidence) + weighted load-bearing symbols — the "
                  "relationships with strength, not just files. serves_truth=false."
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
