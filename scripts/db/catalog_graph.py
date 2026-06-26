#!/usr/bin/env python3
"""Codegraph-style query layer over the OpenHubForAI component graph.

CodeGraph (github.com/colbymchenry/codegraph) pre-indexes a CODE knowledge
graph (symbols + calls/imports/inheritance) into SQLite+FTS5 and serves agents
cheap structural queries (context / callers / impact / trace) so they answer
architecture questions without fanning out across grep/find/Read — ~57% fewer
tokens, ~71% fewer tool calls.

We already have the same substrate one level up: dist/catalog.sqlite holds an
`edges(src_id, rel, dst_id)` adjacency built from component refs (pattern ->
implementing_pipelines, pipeline -> step refs, harness -> packs, etc.) with a
reverse index on dst_id. This module adds the missing query operations, so the
conversational builder and agents can navigate the COMPONENT graph the same
cheap way — and so a component change can compute its blast radius (feeding the
cdc-event-emitter + review tickets).

Operations (mirroring codegraph):
  dependencies(id) -> outgoing edges (what this component uses)
  dependents(id)   -> incoming edges  (codegraph "callers": who uses this)
  context(id)      -> one-call neighborhood (the component + both sides)
  impact(id)       -> transitive dependents (blast radius if this changes)
  trace(a, b)      -> a dependency path from a to b

Build/refresh the underlying graph with: python3 scripts/build_catalog_db.py

Usage:
  python3 -m scripts.db.catalog_graph context tool/codegraph-code-graph-query
  python3 -m scripts.db.catalog_graph dependents tool/agentmemory-persistent-memory
  python3 -m scripts.db.catalog_graph impact adapter/ollama-default
  python3 -m scripts.db.catalog_graph trace pipeline/codegraph-assisted-code-review tool/agentmemory-persistent-memory
  python3 -m scripts.db.catalog_graph --self-test
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import deque
from pathlib import Path

from scripts._config import DIST_DIR

DEFAULT_DB = DIST_DIR / "catalog.sqlite"


def _connect(db: Path) -> sqlite3.Connection:
    if not db.exists():
        raise SystemExit(
            f"{db} not found — build it first: python3 scripts/build_catalog_db.py"
        )
    con = sqlite3.connect(db)
    names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "edges" not in names:
        raise SystemExit(f"{db} has no 'edges' table — rebuild with build_catalog_db.py")
    return con


def dependencies(cid: str, con: sqlite3.Connection) -> list[dict]:
    """Outgoing edges: components that `cid` references/uses."""
    rows = con.execute("SELECT rel, dst_id FROM edges WHERE src_id=? ORDER BY rel, dst_id", (cid,)).fetchall()
    return [{"rel": rel, "id": dst} for rel, dst in rows]


def dependents(cid: str, con: sqlite3.Connection) -> list[dict]:
    """Incoming edges (codegraph 'callers'): components that reference `cid`."""
    rows = con.execute("SELECT rel, src_id FROM edges WHERE dst_id=? ORDER BY rel, src_id", (cid,)).fetchall()
    return [{"rel": rel, "id": src} for rel, src in rows]


def context(cid: str, con: sqlite3.Connection) -> dict:
    """One-call neighborhood: the component plus both edge directions."""
    return {
        "id": cid,
        "dependencies": dependencies(cid, con),
        "dependents": dependents(cid, con),
    }


def impact(cid: str, con: sqlite3.Connection, max_depth: int = 6) -> dict:
    """Transitive dependents — the blast radius if `cid` changes.

    Feeds change-impact review: pair with the cdc-event-emitter to open review
    tickets for affected downstream components when `cid` is updated.
    """
    seen: dict[str, int] = {}
    q: deque[tuple[str, int]] = deque([(cid, 0)])
    while q:
        node, depth = q.popleft()
        if depth >= max_depth:
            continue
        for dep in dependents(node, con):
            if dep["id"] not in seen:
                seen[dep["id"]] = depth + 1
                q.append((dep["id"], depth + 1))
    affected = sorted(seen.items(), key=lambda kv: (kv[1], kv[0]))
    return {
        "id": cid,
        "affected_count": len(affected),
        "affected": [{"id": i, "distance": d} for i, d in affected],
    }


def trace(src: str, dst: str, con: sqlite3.Connection, max_depth: int = 8) -> dict:
    """Shortest dependency path src -> dst over outgoing edges (BFS)."""
    prev: dict[str, str | None] = {src: None}
    q: deque[str] = deque([src])
    while q:
        node = q.popleft()
        if node == dst:
            break
        for dep in dependencies(node, con):
            if dep["id"] not in prev:
                prev[dep["id"]] = node
                q.append(dep["id"])
    if dst not in prev:
        return {"src": src, "dst": dst, "path": None, "reachable": False}
    path = [dst]
    while path[-1] != src:
        path.append(prev[path[-1]])  # type: ignore[arg-type]
    return {"src": src, "dst": dst, "path": list(reversed(path)), "reachable": True}


def _self_test() -> int:
    con = _connect(DEFAULT_DB)
    try:
        total_edges = con.execute("SELECT count(*) FROM edges").fetchone()[0]
        assert total_edges > 0, "edges table is empty — run build_catalog_db.py"
        # Pick a node that has dependents, then exercise every op.
        row = con.execute("SELECT dst_id FROM edges GROUP BY dst_id ORDER BY count(*) DESC LIMIT 1").fetchone()
        hub = row[0]
        ctx = context(hub, con)
        imp = impact(hub, con)
        assert ctx["dependents"], f"expected dependents for hub node {hub}"
        assert imp["affected_count"] >= len(ctx["dependents"]), imp
        # trace from one of hub's dependents back into the graph
        a = ctx["dependents"][0]["id"]
        tr = trace(a, hub, con)
        print(json.dumps({
            "ok": True, "total_edges": total_edges, "hub_node": hub,
            "hub_direct_dependents": len(ctx["dependents"]),
            "hub_blast_radius": imp["affected_count"],
            "sample_trace": tr["path"],
        }, indent=2))
    finally:
        con.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Codegraph-style queries over the component graph.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--db", default=str(DEFAULT_DB))
    sub = p.add_subparsers(dest="op")
    for op in ("dependencies", "dependents", "context", "impact"):
        sp = sub.add_parser(op)
        sp.add_argument("id")
    tp = sub.add_parser("trace")
    tp.add_argument("src")
    tp.add_argument("dst")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()
    if not args.op:
        p.print_help()
        return 1
    con = _connect(Path(args.db))
    try:
        if args.op == "dependencies":
            out = {"id": args.id, "dependencies": dependencies(args.id, con)}
        elif args.op == "dependents":
            out = {"id": args.id, "dependents": dependents(args.id, con)}
        elif args.op == "context":
            out = context(args.id, con)
        elif args.op == "impact":
            out = impact(args.id, con)
        elif args.op == "trace":
            out = trace(args.src, args.dst, con)
    finally:
        con.close()
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
