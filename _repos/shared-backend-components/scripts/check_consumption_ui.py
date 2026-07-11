#!/usr/bin/env python3
"""scripts.check_consumption_ui — proof (C-CONSUME-3): the /consume page renders the full ingestion→consumption
view as a PROJECTION over the API — one "Run CFPB Ingestion → Consumption" button, the required panels, fetches
/api/context/serve + /api/runtime/sections, and computes/stores NO truth itself (no durable writes, no secrets,
no private memory). The page's data source (GET /api/context/serve) is proven to return the reference
ContextResponse. The admin server serves /consume.

CLI: python3 _repos/shared-backend-components/scripts/check_consumption_ui.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
from pathlib import Path

from scripts.api_context_handler import handle

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
_PAGE = _resource("web/baltor/consume.html")
_REQUIRED_PANELS = ("Answer", "Atomic facts", "Held-out", "Receipts", "Freshness", "ContextResponse",
                    "Section maturity", "Provider status", "Conflicts", "Ingestion")
#: a projection-only page must never write durable truth or embed private memory/intel.
_FORBIDDEN = ("durable.db", "INSERT INTO", "UPDATE ", "DELETE FROM", "import sqlite3", "sqlite3.connect",
              ".agent/", "MEMORY.md", "/memory/", "baltor-goal-loop", "OH_SHOWCASE_TOKEN", "sk-")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    check("_repos/baltor/frontend/consume.html exists", _PAGE.exists())
    html = _PAGE.read_text(encoding="utf-8") if _PAGE.exists() else ""
    check("the page has the primary 'Run CFPB Ingestion → Consumption' button", "Run CFPB Ingestion → Consumption" in html)
    check("the page fetches /api/context/serve (the served ContextResponse)", "/api/context/serve" in html)
    check("the page fetches /api/runtime/sections (the maturity scoreboard)", "/api/runtime/sections" in html)
    missing_panels = [p for p in _REQUIRED_PANELS if p not in html]
    check("the page renders the required panels", missing_panels == [], str(missing_panels))
    offenders = [f for f in _FORBIDDEN if f in html]
    check("the page is projection-only (no durable writes / secrets / private memory)", offenders == [], str(offenders))

    # the page's data source actually returns the reference ContextResponse (GET = ungated projection)
    code, resp = handle("GET", "/api/context/serve", {"tenant_id": "demo", "corpus": "cfpb", "require_optimized": "true"})
    check("GET /api/context/serve returns ContextResponse", code == 200 and resp.get("schema_version") == "ContextResponse")
    check("the served answer is '10 business days'", "10 business days" in resp.get("answer", ""))
    served = [f["artifact_id"] for f in resp.get("served_facts", [])]
    held = [h["artifact_id"] for h in resp.get("held_out_warnings", [])]
    check("FAQ-30 shows only as a held-out warning", "fact-faq-30" in held and "fact-faq-30" not in served)
    code2, secs = handle("GET", "/api/runtime/sections", {})
    check("GET /api/runtime/sections feeds the maturity panel", code2 == 200 and secs.get("total", 0) >= 30)

    # the admin server serves /consume (route wired, not a dead link)
    server = (_resource("scripts/baltor_admin_demo_server.py")).read_text(encoding="utf-8")
    check("the admin server serves the /consume page", '"/consume"' in server and "consume.html" in server)

    print(f"\n{'PASS — check_consumption_ui: /consume renders the ingestion→consumption view as a projection over /api/context/serve + /api/runtime/sections (button + panels present); computes no truth; no secrets; the data source returns the reference ContextResponse; the route is served.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: /consume UI.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
