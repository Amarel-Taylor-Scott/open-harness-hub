#!/usr/bin/env python3
"""scripts.check_no_api_consumption_bypass — proof (C-CONSUME-1): no API route serves context truth except
through ConsumptionService. The admin server delegates /api/context/* to the handler and never fabricates
served_facts itself; the handler imports no provider SDK / admin server / raw sqlite and never builds
served_facts (it returns ConsumptionService output); and the routes are registered.

CLI: python3 scripts/check_no_api_consumption_bypass.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    server = (_REPO / "scripts/baltor_admin_demo_server.py").read_text(encoding="utf-8")
    handler = (_REPO / "scripts/api_context_handler.py").read_text(encoding="utf-8")

    # 1) the server delegates context/runtime routes to the handler
    check("admin server delegates the Consumption API to api_context_handler",
          "api_context_handler" in server and "/api/context/serve" in server)
    # 2) the server does NOT fabricate served_facts / a ContextResponse itself
    check("admin server does not fabricate served_facts or a ContextResponse",
          "served_facts" not in server and "ContextResponse(" not in server)
    # 3) the handler is a projection: it never builds served_facts, only returns ConsumptionService output
    check("handler does not construct served_facts (delegates to run_cfpb_to_consumption)",
          "served_facts =" not in handler and "run_cfpb_to_consumption" in handler)
    # 4) the handler reaches no provider SDK / admin server / raw sqlite / global bus
    forbidden = ["import openai", "import anthropic", "baltor_admin_demo_server", "import sqlite3", "sqlite3.connect", "BUS.publish"]
    check("handler reaches no provider SDK / admin / raw sqlite / global bus",
          not any(f in handler for f in forbidden), str([f for f in forbidden if f in handler]))
    # 5) routes registered
    reg = json.loads((_REPO / "architecture/contract_registry.json").read_text())
    routes = {r["route"] for r in reg.get("api_routes", [])}
    need = {"POST /api/context/serve", "GET /api/context/responses/<id>", "GET /api/context/receipts/<id>",
            "GET /api/runtime/sections", "GET /api/runtime/consumption"}
    check("all consumption API routes are registered", need <= routes, str(need - routes))
    check("every registered context route is projection_only", all(r.get("projection_only") for r in reg["api_routes"]))

    print(f"\n{'PASS — check_no_api_consumption_bypass: the admin server delegates to ConsumptionService (no fabricated served_facts); the handler is a projection with no provider/admin/sqlite/bus reach; routes registered + projection-only.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: no API consumption bypass.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
