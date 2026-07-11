#!/usr/bin/env python3
"""primitive_subtree_partitioner — auto-decompose a large primitive into candidate sub-primitives (gap 3.3).

A large primitive is REPRESENTABLE (a source-tree reference, primitive_scale_and_containment) but not
auto-DECOMPOSABLE: finding the sub-primitive boundaries + typed edges inside a 100K-line codebase was an open
problem. This partitions a large primitive's symbol graph (nodes = functions/classes with a module, edges =
calls/imports — the shape `codegraph.py` already produces) into candidate sub-primitives and derives each
one's typed CUT-EDGE interface (entry points = what other partitions call into it; external deps = what it
calls out to).

Partitioner ZOO (extend = one row). The DEFAULT is deterministic + O(n) — the research flagged clustering by
modularity/community detection as the speculative bet (resolution limits, non-unique optima, O(n²)), so:
  - `by_module`       — group symbols by their source module/directory (the natural boundary; O(n), stable).
  - `by_connectivity` — weakly-connected components via union-find (deterministic; isolates independent islands).
  - `community_detection` — a DECLARED SEAM (CNM / label-propagation): richer but non-deterministic + resolution
                            limits; not run here. Race it against the deterministic defaults when it lands.
Every partition is a candidate sub-primitive (`serves_truth=false`); nothing is promoted.

    PYTHONPATH=. python3 scripts/primitive_subtree_partitioner.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  the ONE id authority (data plane law)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"primitive_subtree_partitioner requires canonical_id; import failed: {exc}")

SUBPRIM_ID_PREFIX = "psub"
_CANDIDATE_BITS = {"candidate": True, "serves_truth": False}


# ── partitioners: each maps {symbol_id: node} -> {partition_key: [symbol_ids]}. Deterministic (sorted). ───────
def _partition_by_module(nodes: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    parts: dict[str, list[str]] = {}
    for sid, node in nodes.items():
        parts.setdefault(str(node.get("module") or "unknown"), []).append(sid)
    return {k: sorted(v) for k, v in sorted(parts.items())}


def _partition_by_connectivity(nodes: dict[str, dict[str, Any]],
                               edges: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Weakly-connected components via union-find (edges undirected for grouping). Deterministic keys."""
    parent = {sid: sid for sid in nodes}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)   # deterministic root: the lexicographically-smaller id

    for src, dst in edges:
        if src in parent and dst in parent:
            union(src, dst)
    comps: dict[str, list[str]] = {}
    for sid in nodes:
        comps.setdefault(find(sid), []).append(sid)
    # key each component by its smallest member (stable), sorted
    return {f"component::{root}": sorted(members) for root, members in sorted(comps.items())}


PARTITIONERS: dict[str, dict[str, Any]] = {
    "by_module": {"kind": "deterministic", "needs_edges": False, "fn": _partition_by_module,
                  "note": "group by source module/directory — the natural boundary; O(n), the default"},
    "by_connectivity": {"kind": "deterministic", "needs_edges": True, "fn": _partition_by_connectivity,
                        "note": "weakly-connected components (union-find) — isolate independent islands"},
    "community_detection": {"kind": "seam", "needs_edges": True, "fn": None,
                            "note": "CNM / label-propagation modularity clustering — richer but "
                                    "non-deterministic + resolution-limited; declared, not run"},
}


def derive_interface(partition_members: list[str], all_partition_of: dict[str, str],
                     edges: list[tuple[str, str]]) -> dict[str, Any]:
    """The typed CUT-EDGE interface of a partition: entry_points = its symbols called FROM another partition
    (its public API / inputs); external_deps = symbols in OTHER partitions it calls (its required outputs/
    dependencies). These cut-edges are the candidate sub-primitive's input/output contract."""
    members = set(partition_members)
    entry_points: set[str] = set()
    external_deps: set[str] = set()
    for src, dst in edges:
        src_in = src in members
        dst_in = dst in members
        if dst_in and not src_in:            # something outside calls IN -> dst is an entry point
            entry_points.add(dst)
        if src_in and not dst_in:            # a member calls OUT -> dst is an external dependency
            external_deps.add(dst)
    return {"entry_points": sorted(entry_points), "external_deps": sorted(external_deps),
            "input_edges": sorted(entry_points), "output_edges": sorted(external_deps)}


def partition_symbol_graph(nodes: dict[str, dict[str, Any]], edges: list[tuple[str, str]], *,
                           method: str = "by_module") -> dict[str, Any]:
    """Partition a large primitive's symbol graph into candidate sub-primitives + their cut-edge interfaces."""
    spec = PARTITIONERS[method]
    if spec["kind"] == "seam" or spec["fn"] is None:
        return {"method": method, "seam": True, "note": spec["note"], "sub_primitives": [], **_CANDIDATE_BITS}
    parts = spec["fn"](nodes, edges) if spec["needs_edges"] else spec["fn"](nodes)
    partition_of = {sid: key for key, members in parts.items() for sid in members}
    sub_primitives = []
    for key, members in parts.items():
        interface = derive_interface(members, partition_of, edges)
        sub_primitives.append({
            "sub_primitive_id": canonical_id(SUBPRIM_ID_PREFIX, method, key),
            "record_type": "candidate_sub_primitive", "partition_key": key,
            "n_symbols": len(members), "symbols": members, "interface": interface,
            "note": "a candidate sub-primitive carved from a large primitive's call graph; its cut-edges are "
                    "its typed interface — review + verify before treating as a standalone primitive",
            **_CANDIDATE_BITS})
    # a cut edge is any edge whose endpoints fall in different partitions — the total decomposition seam size.
    cut_edges = [(s, d) for s, d in edges if partition_of.get(s) != partition_of.get(d)]
    return {"method": method, "n_partitions": len(parts), "n_symbols": len(nodes),
            "n_cut_edges": len(cut_edges), "cut_fraction": round(len(cut_edges) / max(1, len(edges)), 4),
            "sub_primitives": sub_primitives, "note": "lower cut_fraction = cleaner decomposition (fewer "
            "cross-partition dependencies)", **_CANDIDATE_BITS}


def _synthetic_graph() -> tuple[dict[str, dict[str, Any]], list[tuple[str, str]]]:
    """A synthetic large-primitive symbol graph: 3 cohesive modules (api, worker, db) with a few cross-module
    calls (the natural cut edges) and one isolated helper island."""
    nodes = {
        "api.handle": {"module": "api"}, "api.route": {"module": "api"}, "api.serialize": {"module": "api"},
        "worker.run": {"module": "worker"}, "worker.step": {"module": "worker"},
        "db.query": {"module": "db"}, "db.connect": {"module": "db"},
        "util.lonely": {"module": "util"},   # an isolated island (no edges) -> its own component
    }
    edges = [
        ("api.handle", "api.route"), ("api.route", "api.serialize"),   # intra-api
        ("worker.run", "worker.step"),                                  # intra-worker
        ("db.query", "db.connect"),                                     # intra-db
        ("api.handle", "worker.run"),    # cross: api -> worker  (a cut edge)
        ("worker.step", "db.query"),     # cross: worker -> db   (a cut edge)
    ]
    return nodes, edges


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    nodes, edges = _synthetic_graph()

    # (1) by_module: 4 modules -> 4 candidate sub-primitives, deterministically.
    by_mod = partition_symbol_graph(nodes, edges, method="by_module")
    keys = {sp["partition_key"] for sp in by_mod["sub_primitives"]}
    checks.append(("by_module partitions the graph into one candidate sub-primitive per module (api/worker/db/"
                   "util), deterministically",
                   by_mod["n_partitions"] == 4 and keys == {"api", "worker", "db", "util"}
                   and by_mod["n_symbols"] == 8, f"partitions={sorted(keys)}"))

    # (2) the CUT-EDGE interface is derived: the api partition's external_deps includes worker.run (it calls
    #     out), the worker partition's entry_points includes worker.run (api calls in). Real interfaces.
    api = next(sp for sp in by_mod["sub_primitives"] if sp["partition_key"] == "api")
    worker = next(sp for sp in by_mod["sub_primitives"] if sp["partition_key"] == "worker")
    checks.append(("typed cut-edge interfaces derived: api.external_deps has worker.run (calls out); "
                   "worker.entry_points has worker.run (called in) — the sub-primitive's I/O contract",
                   "worker.run" in api["interface"]["external_deps"]
                   and "worker.run" in worker["interface"]["entry_points"]
                   and "db.query" in worker["interface"]["external_deps"],
                   json.dumps(worker["interface"])[:150]))

    # (3) the cut edges are exactly the 2 cross-module calls (a clean decomposition metric).
    checks.append(("cut edges = exactly the cross-partition calls (2 of 6); cut_fraction reports decomposition "
                   "cleanliness",
                   by_mod["n_cut_edges"] == 2 and by_mod["cut_fraction"] == round(2 / 6, 4),
                   f"cut={by_mod['n_cut_edges']}/{len(edges)}"))

    # (4) by_connectivity: the isolated util.lonely is its own component; api+worker+db are one connected blob.
    by_conn = partition_symbol_graph(nodes, edges, method="by_connectivity")
    sizes = sorted(sp["n_symbols"] for sp in by_conn["sub_primitives"])
    checks.append(("by_connectivity isolates the disconnected island (util.lonely alone) from the connected "
                   "api+worker+db component",
                   by_conn["n_partitions"] == 2 and sizes == [1, 7], f"component sizes={sizes}"))

    # (5) determinism: same graph -> identical partitions + ids twice.
    a = json.dumps(partition_symbol_graph(nodes, edges, method="by_module"), sort_keys=True)
    b = json.dumps(partition_symbol_graph(nodes, edges, method="by_module"), sort_keys=True)
    checks.append(("deterministic: identical partitions + sub-primitive ids on re-run", a == b, ""))

    # (6) every sub-primitive is candidate-only; the community-detection lane is a declared seam, not run.
    seam = partition_symbol_graph(nodes, edges, method="community_detection")
    checks.append(("every sub-primitive candidate-only; community_detection is a DECLARED seam (not run)",
                   all(sp["serves_truth"] is False for sp in by_mod["sub_primitives"])
                   and seam.get("seam") is True and PARTITIONERS["community_detection"]["kind"] == "seam", ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - primitive_subtree_partitioner: auto-decompose a large primitive's "
          f"symbol graph into candidate sub-primitives + typed cut-edge interfaces (gap 3.3) — deterministic "
          f"by_module (default) + by_connectivity; community detection a declared seam; entry-points/deps ARE "
          f"the sub-primitive I/O contract; cut_fraction reports decomposition cleanliness. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Partition a large primitive's symbol graph into sub-primitives.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--method", default="by_module", choices=list(PARTITIONERS))
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    nodes, edges = _synthetic_graph()
    print(json.dumps(partition_symbol_graph(nodes, edges, method=args.method), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
