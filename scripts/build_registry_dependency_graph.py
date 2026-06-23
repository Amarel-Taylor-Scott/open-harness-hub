"""build_registry_dependency_graph — the META-REGISTRY (registry #83): the ontology layer governing the ontology.

COMPUTES (never hand-types) a dependency graph from architecture/registry_ontology.json: nodes = every registry
(with status/layer/kind/backing_count), edges = references one registry makes to another (parsed from the '#N'
mentions in its distinct_from + gap_to_close). Answers "which registries depend on / relate to which" and
"what's most depended-on" — the Registry-Registry + Registry-Dependency-Graph the owner asked for, derived from
real cross-references so it can't drift.

  python3 scripts/build_registry_dependency_graph.py            # (re)write architecture/registry_dependency_graph.json
  python3 scripts/build_registry_dependency_graph.py --self-test # regenerate + validate consistency + freshness

Deterministic, offline, stdlib only. serves_truth=false.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_ONT = _REPO / "architecture" / "registry_ontology.json"
_OUT = _REPO / "architecture" / "registry_dependency_graph.json"
_REF_RE = re.compile(r"#(\d+)")
_TOP_N = 8


def _reverse_map(block: dict) -> dict[int, str]:
    """registry n -> the block-key it belongs to (for universes / registry_kinds id-list blocks)."""
    out: dict[int, str] = {}
    for key, v in block.items():
        if isinstance(v, dict) and "registry_ids" in v:
            for n in v["registry_ids"]:
                out[n] = key
    return out


def build_graph(doc: dict) -> dict:
    regs = doc.get("registries", [])
    layer_of = _reverse_map(doc.get("universes", {}))
    kind_of = _reverse_map(doc.get("registry_kinds", {}))
    valid_ns = {r["n"] for r in regs}

    nodes, edges = [], []
    indeg: dict[int, int] = {r["n"]: 0 for r in regs}
    for r in regs:
        n = r["n"]
        # distinct_from: numbers are ALWAYS registry refs ("vs 71 external_systems"). gap_to_close: only
        # explicit #N (bare numbers there are counts like "14 portals"), so don't over-match.
        df_refs = {int(m) for m in re.findall(r"\d+", r.get("distinct_from", ""))}
        gc_refs = {int(m) for m in _REF_RE.findall(r.get("gap_to_close", ""))}
        refs = sorted((df_refs | gc_refs) & valid_ns - {n})
        nodes.append({
            "n": n, "id": r["id"], "status": r["status"],
            "layer": layer_of.get(n, "?"), "kind": kind_of.get(n, "?"),
            "backing_count": len(r.get("backing", [])), "refs": refs,
        })
        for to in refs:
            edges.append({"from": n, "from_id": r["id"], "to": to})
            indeg[to] += 1

    id_of = {r["n"]: r["id"] for r in regs}
    most_depended = sorted(
        ({"n": n, "id": id_of[n], "in_degree": d} for n, d in indeg.items() if d > 0),
        key=lambda x: (-x["in_degree"], x["n"]),
    )[:_TOP_N]
    return {
        "version": "0.1.0",
        "principle": "META-REGISTRY (registry #83): dependency graph COMPUTED from registry_ontology cross-refs "
                     "(the #N mentions in distinct_from + gap_to_close). The ontology layer governing the ontology; "
                     "regenerate with scripts/build_registry_dependency_graph.py. serves_truth=false.",
        "serves_truth": False,
        "generated_from": "architecture/registry_ontology.json",
        "stats": {
            "node_count": len(nodes), "edge_count": len(edges),
            "by_status": {s: sum(1 for x in nodes if x["status"] == s) for s in ("live", "partial", "gap")},
            "most_depended_on": most_depended,
        },
        "nodes": nodes,
        "edges": edges,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true", help="regenerate + validate consistency + freshness; exit nonzero on failure")
    args = ap.parse_args()
    doc = json.loads(_ONT.read_text())
    graph = build_graph(doc)

    if not args.self_test:
        _OUT.write_text(json.dumps(graph, indent=2) + "\n")
        print(f"wrote {_OUT.relative_to(_REPO)}: {graph['stats']['node_count']} nodes, {graph['stats']['edge_count']} edges")
        return 0

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    ns = {nd["n"] for nd in graph["nodes"]}
    ck("node per registry", len(graph["nodes"]) == len(doc.get("registries", [])))
    ck("every edge target is a real registry", all(e["to"] in ns for e in graph["edges"]))
    ck("every edge source is a real registry", all(e["from"] in ns for e in graph["edges"]))
    ck("no self-edges", all(e["from"] != e["to"] for e in graph["edges"]))
    ck("graph has dependency edges", graph["stats"]["edge_count"] >= 1, str(graph["stats"]["edge_count"]))
    ck("serves_truth is false", graph["serves_truth"] is False)
    # freshness: the on-disk file must equal the regenerated graph (computed-not-typed, no drift)
    on_disk = json.loads(_OUT.read_text()) if _OUT.exists() else None
    ck("on-disk graph is fresh (regenerate to fix)", on_disk == graph)

    if fails:
        print(f"\nFAIL - build_registry_dependency_graph: {len(fails)} of {checks} assertions failed")
        return 1
    top = ", ".join(f"#{d['n']} {d['id']}({d['in_degree']})" for d in graph["stats"]["most_depended_on"][:4])
    print(f"PASS - build_registry_dependency_graph: {graph['stats']['node_count']} nodes, "
          f"{graph['stats']['edge_count']} edges, fresh; most-depended-on: {top}; {checks} assertions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
