"""knowledge.dependency_graph — Dependency Graph Intelligence (the owner's Registry #92 / §3).

Most repos are not isolated — everything depends on something. This builds a directed dependency graph from declared
'package -> requires' edges (seeded from _repos/shared-backend-components/architecture/package_dependency_seed.json; full graph scraped from PyPI/npm
manifests via #91) and answers the reinvention question at the STACK level: 'why build a custom PDF parser — this
whole dependency stack (ocrmypdf -> pikepdf/pdfminer/pillow/tesseract) already provides it?'

Deterministic (no model): transitive closure, cycle detection, ecosystem clusters (connected components), and
capability coverage ('which existing package, with its transitive deps, already provides these capabilities?').
serves_truth=false; a match is a governed CANDIDATE ('this stack likely covers it — verify'), never an assertion.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path

py_var_src_teleon_knowledge_dependency_graph___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
py_var_src_teleon_knowledge_dependency_graph___SEED = _resource("architecture") / "package_dependency_seed.json"


def py_function_src_teleon_knowledge_dependency_graph__load_packages() -> list[dict]:
    return json.loads(py_var_src_teleon_knowledge_dependency_graph___SEED.read_text())["packages"]


def py_function_src_teleon_knowledge_dependency_graph__build_graph(py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__build_graph__packages: list[dict] | None = None) -> dict:
    """Directed graph: {nodes: {id: record}, edges: {id: [requires...]}, provides: {capability: [ids]}}."""
    py_local_src_teleon_knowledge_dependency_graph__build_graph__pkgs = py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__build_graph__packages if py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__build_graph__packages is not None else py_function_src_teleon_knowledge_dependency_graph__load_packages()
    py_local_src_teleon_knowledge_dependency_graph__build_graph__nodes = {py_local_src_teleon_knowledge_dependency_graph__build_graph__p["id"]: py_local_src_teleon_knowledge_dependency_graph__build_graph__p for py_local_src_teleon_knowledge_dependency_graph__build_graph__p in py_local_src_teleon_knowledge_dependency_graph__build_graph__pkgs}
    py_local_src_teleon_knowledge_dependency_graph__build_graph__edges = {py_local_src_teleon_knowledge_dependency_graph__build_graph__p["id"]: list(py_local_src_teleon_knowledge_dependency_graph__build_graph__p.get("requires", [])) for py_local_src_teleon_knowledge_dependency_graph__build_graph__p in py_local_src_teleon_knowledge_dependency_graph__build_graph__pkgs}
    py_local_src_teleon_knowledge_dependency_graph__build_graph__provides: dict[str, list[str]] = {}
    for py_local_src_teleon_knowledge_dependency_graph__build_graph__p in py_local_src_teleon_knowledge_dependency_graph__build_graph__pkgs:
        for py_local_src_teleon_knowledge_dependency_graph__build_graph__cap in py_local_src_teleon_knowledge_dependency_graph__build_graph__p.get("provides", []):
            py_local_src_teleon_knowledge_dependency_graph__build_graph__provides.setdefault(py_local_src_teleon_knowledge_dependency_graph__build_graph__cap, []).append(py_local_src_teleon_knowledge_dependency_graph__build_graph__p["id"])
    return {"nodes": py_local_src_teleon_knowledge_dependency_graph__build_graph__nodes, "edges": py_local_src_teleon_knowledge_dependency_graph__build_graph__edges, "provides": py_local_src_teleon_knowledge_dependency_graph__build_graph__provides}


def py_function_src_teleon_knowledge_dependency_graph__transitive_deps(py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__transitive_deps__graph: dict, py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__transitive_deps__node: str) -> list[str]:
    """All packages reachable from `node` (its full dependency closure), excluding `node`. Cycle-safe."""
    py_local_src_teleon_knowledge_dependency_graph__transitive_deps__seen: set[str] = set()
    py_local_src_teleon_knowledge_dependency_graph__transitive_deps__stack = list(py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__transitive_deps__graph["edges"].get(py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__transitive_deps__node, []))
    while py_local_src_teleon_knowledge_dependency_graph__transitive_deps__stack:
        py_local_src_teleon_knowledge_dependency_graph__transitive_deps__d = py_local_src_teleon_knowledge_dependency_graph__transitive_deps__stack.pop()
        if py_local_src_teleon_knowledge_dependency_graph__transitive_deps__d in py_local_src_teleon_knowledge_dependency_graph__transitive_deps__seen:
            continue
        py_local_src_teleon_knowledge_dependency_graph__transitive_deps__seen.add(py_local_src_teleon_knowledge_dependency_graph__transitive_deps__d)
        py_local_src_teleon_knowledge_dependency_graph__transitive_deps__stack.extend(py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__transitive_deps__graph["edges"].get(py_local_src_teleon_knowledge_dependency_graph__transitive_deps__d, []))
    py_local_src_teleon_knowledge_dependency_graph__transitive_deps__seen.discard(py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__transitive_deps__node)
    return sorted(py_local_src_teleon_knowledge_dependency_graph__transitive_deps__seen)


def py_function_src_teleon_knowledge_dependency_graph__detect_cycle(py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__detect_cycle__graph: dict) -> list[str]:
    """Return one cycle (node ids) if the dependency graph has one, else []."""
    py_local_src_teleon_knowledge_dependency_graph__detect_cycle__WHITE, py_local_src_teleon_knowledge_dependency_graph__detect_cycle__GREY, py_local_src_teleon_knowledge_dependency_graph__detect_cycle__BLACK = 0, 1, 2
    py_local_src_teleon_knowledge_dependency_graph__detect_cycle__color = {py_local_src_teleon_knowledge_dependency_graph__detect_cycle__n: py_local_src_teleon_knowledge_dependency_graph__detect_cycle__WHITE for py_local_src_teleon_knowledge_dependency_graph__detect_cycle__n in py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__detect_cycle__graph["edges"]}
    py_local_src_teleon_knowledge_dependency_graph__detect_cycle__path: list[str] = []

    def visit(py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__detect_cycle_visit__n: str) -> list[str]:
        if py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__detect_cycle_visit__n not in py_local_src_teleon_knowledge_dependency_graph__detect_cycle__color:  # external dep not in our node set
            return []
        py_local_src_teleon_knowledge_dependency_graph__detect_cycle__color[py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__detect_cycle_visit__n] = py_local_src_teleon_knowledge_dependency_graph__detect_cycle__GREY
        py_local_src_teleon_knowledge_dependency_graph__detect_cycle__path.append(py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__detect_cycle_visit__n)
        for py_local_src_teleon_knowledge_dependency_graph__detect_cycle_visit__d in py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__detect_cycle__graph["edges"].get(py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__detect_cycle_visit__n, []):
            if py_local_src_teleon_knowledge_dependency_graph__detect_cycle__color.get(py_local_src_teleon_knowledge_dependency_graph__detect_cycle_visit__d) == py_local_src_teleon_knowledge_dependency_graph__detect_cycle__GREY:
                return py_local_src_teleon_knowledge_dependency_graph__detect_cycle__path[py_local_src_teleon_knowledge_dependency_graph__detect_cycle__path.index(py_local_src_teleon_knowledge_dependency_graph__detect_cycle_visit__d):] + [py_local_src_teleon_knowledge_dependency_graph__detect_cycle_visit__d]
            if py_local_src_teleon_knowledge_dependency_graph__detect_cycle__color.get(py_local_src_teleon_knowledge_dependency_graph__detect_cycle_visit__d, py_local_src_teleon_knowledge_dependency_graph__detect_cycle__BLACK) == py_local_src_teleon_knowledge_dependency_graph__detect_cycle__WHITE:
                py_local_src_teleon_knowledge_dependency_graph__detect_cycle_visit__c = visit(py_local_src_teleon_knowledge_dependency_graph__detect_cycle_visit__d)
                if py_local_src_teleon_knowledge_dependency_graph__detect_cycle_visit__c:
                    return py_local_src_teleon_knowledge_dependency_graph__detect_cycle_visit__c
        py_local_src_teleon_knowledge_dependency_graph__detect_cycle__path.pop()
        py_local_src_teleon_knowledge_dependency_graph__detect_cycle__color[py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__detect_cycle_visit__n] = py_local_src_teleon_knowledge_dependency_graph__detect_cycle__BLACK
        return []

    for py_local_src_teleon_knowledge_dependency_graph__detect_cycle__n in list(py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__detect_cycle__graph["edges"]):
        if py_local_src_teleon_knowledge_dependency_graph__detect_cycle__color[py_local_src_teleon_knowledge_dependency_graph__detect_cycle__n] == py_local_src_teleon_knowledge_dependency_graph__detect_cycle__WHITE:
            py_local_src_teleon_knowledge_dependency_graph__detect_cycle__c = visit(py_local_src_teleon_knowledge_dependency_graph__detect_cycle__n)
            if py_local_src_teleon_knowledge_dependency_graph__detect_cycle__c:
                return py_local_src_teleon_knowledge_dependency_graph__detect_cycle__c
    return []


def py_function_src_teleon_knowledge_dependency_graph__ecosystem_cluster(py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__ecosystem_cluster__graph: dict, py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__ecosystem_cluster__node: str) -> list[str]:
    """The connected component (undirected) around `node` — its ecosystem cluster."""
    py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__adj: dict[str, set[str]] = {}
    for py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__src, py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__deps in py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__ecosystem_cluster__graph["edges"].items():
        for py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__d in py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__deps:
            py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__adj.setdefault(py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__src, set()).add(py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__d)
            py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__adj.setdefault(py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__d, set()).add(py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__src)
    py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__seen = {py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__ecosystem_cluster__node}
    py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__stack = [py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__ecosystem_cluster__node]
    while py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__stack:
        py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__n = py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__stack.pop()
        for py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__m in py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__adj.get(py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__n, ()):
            if py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__m not in py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__seen:
                py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__seen.add(py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__m)
                py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__stack.append(py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__m)
    return sorted(py_local_src_teleon_knowledge_dependency_graph__ecosystem_cluster__seen)


def py_function_src_teleon_knowledge_dependency_graph__stack_exists(py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__stack_exists__capabilities: list[str], py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__stack_exists__graph: dict | None = None) -> dict:
    """Does an existing package (with its transitive deps) already cover ALL requested capabilities? The stack-level
    reinvention check. Returns the covering packages + a governed candidate verdict."""
    py_local_src_teleon_knowledge_dependency_graph__stack_exists__g = py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__stack_exists__graph if py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__stack_exists__graph is not None else py_function_src_teleon_knowledge_dependency_graph__build_graph()
    py_local_src_teleon_knowledge_dependency_graph__stack_exists__wanted = set(py_arg_src_teleon_knowledge_dependency_graph__py_function_src_teleon_knowledge_dependency_graph__stack_exists__capabilities)
    py_local_src_teleon_knowledge_dependency_graph__stack_exists__covering = []
    for py_local_src_teleon_knowledge_dependency_graph__stack_exists__nid, py_local_src_teleon_knowledge_dependency_graph__stack_exists__rec in py_local_src_teleon_knowledge_dependency_graph__stack_exists__g["nodes"].items():
        py_local_src_teleon_knowledge_dependency_graph__stack_exists__covered = set(py_local_src_teleon_knowledge_dependency_graph__stack_exists__rec.get("provides", []))
        for py_local_src_teleon_knowledge_dependency_graph__stack_exists__dep in py_function_src_teleon_knowledge_dependency_graph__transitive_deps(py_local_src_teleon_knowledge_dependency_graph__stack_exists__g, py_local_src_teleon_knowledge_dependency_graph__stack_exists__nid):
            py_local_src_teleon_knowledge_dependency_graph__stack_exists__covered |= set(py_local_src_teleon_knowledge_dependency_graph__stack_exists__g["nodes"].get(py_local_src_teleon_knowledge_dependency_graph__stack_exists__dep, {}).get("provides", []))
        if py_local_src_teleon_knowledge_dependency_graph__stack_exists__wanted <= py_local_src_teleon_knowledge_dependency_graph__stack_exists__covered:
            py_local_src_teleon_knowledge_dependency_graph__stack_exists__covering.append({"package": py_local_src_teleon_knowledge_dependency_graph__stack_exists__nid, "transitive_deps": py_function_src_teleon_knowledge_dependency_graph__transitive_deps(py_local_src_teleon_knowledge_dependency_graph__stack_exists__g, py_local_src_teleon_knowledge_dependency_graph__stack_exists__nid),
                             "provides": sorted(py_local_src_teleon_knowledge_dependency_graph__stack_exists__covered & py_local_src_teleon_knowledge_dependency_graph__stack_exists__wanted)})
    return {
        "capabilities": sorted(py_local_src_teleon_knowledge_dependency_graph__stack_exists__wanted),
        "stack_exists": bool(py_local_src_teleon_knowledge_dependency_graph__stack_exists__covering),
        "covering_packages": py_local_src_teleon_knowledge_dependency_graph__stack_exists__covering,
        "verdict": ("a dependency stack already provides this — don't rebuild it (verify fit)" if py_local_src_teleon_knowledge_dependency_graph__stack_exists__covering
                    else "no single existing stack covers all of these — may be genuinely novel"),
        "serves_truth": False, "candidate": True,
    }


def _self_test() -> list[str]:
    py_local_src_teleon_knowledge_dependency_graph__self_test__fails = []

    def ck(py_arg_src_teleon_knowledge_dependency_graph__self_test_ck__name, py_arg_src_teleon_knowledge_dependency_graph__self_test_ck__ok):
        if not py_arg_src_teleon_knowledge_dependency_graph__self_test_ck__ok:
            py_local_src_teleon_knowledge_dependency_graph__self_test__fails.append(f"dependency_graph: {py_arg_src_teleon_knowledge_dependency_graph__self_test_ck__name}")
            print(f"  [XX] dependency_graph: {py_arg_src_teleon_knowledge_dependency_graph__self_test_ck__name}")

    py_local_src_teleon_knowledge_dependency_graph__self_test__g = py_function_src_teleon_knowledge_dependency_graph__build_graph()
    ck("graph has nodes + edges + provides", py_local_src_teleon_knowledge_dependency_graph__self_test__g["nodes"] and py_local_src_teleon_knowledge_dependency_graph__self_test__g["edges"] and py_local_src_teleon_knowledge_dependency_graph__self_test__g["provides"])
    ck("transitive closure reaches indirect deps", "lxml" in py_function_src_teleon_knowledge_dependency_graph__transitive_deps(py_local_src_teleon_knowledge_dependency_graph__self_test__g, "ocrmypdf"))
    ck("transitive closure excludes self", "ocrmypdf" not in py_function_src_teleon_knowledge_dependency_graph__transitive_deps(py_local_src_teleon_knowledge_dependency_graph__self_test__g, "ocrmypdf"))
    ck("no false cycle in an acyclic seed", py_function_src_teleon_knowledge_dependency_graph__detect_cycle(py_local_src_teleon_knowledge_dependency_graph__self_test__g) == [])
    # inject a cycle -> detected
    py_local_src_teleon_knowledge_dependency_graph__self_test__cyc = py_function_src_teleon_knowledge_dependency_graph__build_graph([{"id": "a", "requires": ["b"], "provides": []},
                       {"id": "b", "requires": ["a"], "provides": []}])
    ck("detects an injected cycle", len(py_function_src_teleon_knowledge_dependency_graph__detect_cycle(py_local_src_teleon_knowledge_dependency_graph__self_test__cyc)) >= 2)
    ck("ecosystem cluster groups the pdf stack", "pdfminer-six" in py_function_src_teleon_knowledge_dependency_graph__ecosystem_cluster(py_local_src_teleon_knowledge_dependency_graph__self_test__g, "ocrmypdf"))
    py_local_src_teleon_knowledge_dependency_graph__self_test__se = py_function_src_teleon_knowledge_dependency_graph__stack_exists(["ocr", "pdf_text_extraction"], py_local_src_teleon_knowledge_dependency_graph__self_test__g)
    ck("stack_exists finds the ocr+pdf stack (ocrmypdf)", py_local_src_teleon_knowledge_dependency_graph__self_test__se["stack_exists"] and any(
        c["package"] == "ocrmypdf" for c in py_local_src_teleon_knowledge_dependency_graph__self_test__se["covering_packages"]))
    ck("stack_exists honest on a novel combo", not py_function_src_teleon_knowledge_dependency_graph__stack_exists(["time_travel", "telepathy"], py_local_src_teleon_knowledge_dependency_graph__self_test__g)["stack_exists"])
    ck("verdict is a governed candidate", py_local_src_teleon_knowledge_dependency_graph__self_test__se["serves_truth"] is False and py_local_src_teleon_knowledge_dependency_graph__self_test__se["candidate"])
    return py_local_src_teleon_knowledge_dependency_graph__self_test__fails
