#!/usr/bin/env python3
"""scripts.check_live_supervisor_ui — proof (OPP-supervisor-scaling-live, UI): the /fleet page exists, is
PROJECTION-ONLY (GET reads only — no POST/PUT/DELETE writes), reads the /api/fleet endpoints, and shows the
required panels. The admin server routes /fleet to it.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_live_supervisor_ui.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
_PAGE = _resource("web/baltor/fleet.html")
_PANELS = ["Supervisor instances", "Shard ownership", "Failovers", "ticks", "Decisions", "Capacity",
           "Durable task queue", "Spawn requests"]


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    chk("fleet.html exists", _PAGE.exists())
    html = _PAGE.read_text() if _PAGE.exists() else ""
    chk("reads /api/fleet (projection)", "/api/fleet" in html)
    chk("declares projection-only", "projection-only" in html.lower() or "PROJECTION-ONLY" in html)
    for p in _PANELS:
        chk(f"panel present: {p}", p.lower() in html.lower())
    # projection-only: no write verbs in the page's fetches
    writes = [v for v in ("method: 'POST'", 'method:"POST"', "method: 'PUT'", "method: 'DELETE'", "XMLHttpRequest") if v in html]
    chk("no write requests (GET-only)", writes == [], str(writes))

    # the admin server routes /fleet to the page + exposes /api/fleet
    srv = (_resource("scripts/baltor_admin_demo_server.py")).read_text()
    chk("admin server routes /fleet", '"/fleet"' in srv and 'fleet.html' in srv)
    chk("admin server exposes /api/fleet", "/api/fleet" in srv)

    print(f"\n{'PASS — check_live_supervisor_ui: /fleet page exists, projection-only (GET reads), shows the fleet panels, routed by the admin server.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
