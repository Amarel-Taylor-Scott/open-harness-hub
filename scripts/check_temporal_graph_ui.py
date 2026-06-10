#!/usr/bin/env python3
"""scripts.check_temporal_graph_ui — proof: /temporal-graph is a projection-only page over
/api/graph/temporal/* with the required panels, no forbidden tokens, no durable writes/secrets.

CLI: PYTHONPATH=. python3 scripts/check_temporal_graph_ui.py --self-test
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

_PAGE = Path(__file__).resolve().parents[1] / "web" / "baltor" / "temporal-graph.html"
_FORBIDDEN = (".agent/", "MEMORY.md", "baltor-goal-loop", ".claude/", "INSERT INTO", "UPDATE ", "DELETE FROM",
              "sqlite3", "localStorage", "sessionStorage", "indexedDB", "OH_SHOWCASE_TOKEN")
_PANELS = ("Current served facts", "Held-out claims", "Contradictions", "Fact timeline", "Governance edges",
           "Provider status", "Reconciliation")


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    chk("temporal-graph.html exists", _PAGE.exists())
    t = _PAGE.read_text(encoding="utf-8")
    # fetches only /api/graph/temporal/*
    urls = re.findall(r'"(/api/[^"]+)"', t)
    chk("fetches at least one /api/graph/temporal route", any(u.startswith("/api/graph/temporal/") for u in urls))
    chk("fetches ONLY /api/graph/temporal/* (no foreign API)", all(u.startswith("/api/graph/temporal/") for u in urls), str([u for u in urls if not u.startswith("/api/graph/temporal/")]))
    for bad in _FORBIDDEN:
        chk(f"no forbidden token {bad!r}", bad not in t)
    for panel in _PANELS:
        chk(f"panel present: {panel}", panel in t)
    chk("has loading + error states", "building" in t and "error" in t.lower())
    chk("has the Build Temporal CFPB Graph button", "Build Temporal CFPB Graph" in t)
    chk("no secret-shaped literal", not re.search(r"sk-[A-Za-z0-9]{16}", t) and '"api_key"' not in t)

    print(f"\n{'PASS — check_temporal_graph_ui: /temporal-graph is projection-only over /api/graph/temporal/*; all panels present; loading/error states; no forbidden tokens/secrets/durable writes.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: temporal graph UI.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
