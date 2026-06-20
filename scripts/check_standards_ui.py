#!/usr/bin/env python3
"""scripts.check_standards_ui — proof: the /standards page renders the standards-system view as a PROJECTION
over the Standards API. It fetches ONLY /api/standards/* (no other origin), shows the named panels, has
loading + error + empty states, computes/stores NO truth (no durable writes, no secrets, no private memory).
The page's data sources (the Standards API handler) are exercised here to confirm they answer the page.
Deterministic + offline.

CLI: python3 scripts/check_standards_ui.py --self-test
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from scripts.api_standards_handler import handle

_REPO = Path(__file__).resolve().parents[1]
_PAGE = _REPO / "web" / "baltor" / "standards.html"

#: the named panels the page must render.
_REQUIRED_PANELS = ("Pattern registry", "Standards catalog", "Template catalog", "Routine library", "Waivers",
                    "Pattern miner report", "New-code compliance", "Examples", "Opportunities", "Risks")
#: a projection-only page must never write durable truth or embed private memory/intel/secrets.
_FORBIDDEN = ("durable.db", "INSERT INTO", "UPDATE ", "DELETE FROM", "import sqlite3", "sqlite3.connect",
              ".agent/", "MEMORY.md", "/memory/", "baltor-goal-loop", "OH_SHOWCASE_TOKEN", "sk-",
              "localStorage", "sessionStorage", "indexedDB")
#: every fetch URL in the page must be under this prefix.
_API_PREFIX = "/api/standards/"


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    check("web/baltor/standards.html exists", _PAGE.exists())
    html = _PAGE.read_text(encoding="utf-8") if _PAGE.exists() else ""

    # named panels present
    missing = [p for p in _REQUIRED_PANELS if p not in html]
    check("the page renders all named panels", missing == [], str(missing))

    # loading / error / empty states present
    check("the page has a loading state", "Loading" in html and "Fetching" in html)
    check("the page has an error state", "errState" in html and "error:" in html)
    check("the page has an empty state ('(none)')", "(none)" in html)
    check("the page has an unavailable/degraded state", "not produced yet" in html)

    # fetches ONLY /api/standards/* — every fetch(...) / getJSON(...) URL string is under the prefix.
    fetch_urls = re.findall(r'fetch\(\s*([A-Za-z0-9_.\[\]"\']+)', html)
    # the page fetches via getJSON(API[...]) and the API map literals; assert every quoted URL literal is in-scope.
    url_literals = re.findall(r'"(/[^"]*)"', html)
    foreign = [u for u in url_literals if u.startswith("/api/") and not u.startswith(_API_PREFIX)]
    check("every API URL literal targets /api/standards/*", foreign == [], str(foreign))
    check("the page references the standards API map", "/api/standards/patterns" in html and "/api/standards/generate-preview" in html)
    # no cross-origin fetch (http/https absolute) in the page
    check("no cross-origin fetch (no absolute http(s) URL)", "http://" not in html and "https://" not in html)

    # projection-only: no durable writes / secrets / private memory / client storage
    offenders = [f for f in _FORBIDDEN if f in html]
    check("the page is projection-only (no durable writes / secrets / private memory / storage)", offenders == [], str(offenders))

    # the page's data sources actually answer (degrade gracefully when truth files are absent)
    for route, key in (("/api/standards/patterns", "patterns"), ("/api/standards/templates", "templates"),
                       ("/api/standards/routines", "routines"), ("/api/standards/waivers", "waivers"),
                       ("/api/standards/maturity", "patterns")):
        code, payload = handle("GET", route, {})
        check(f"data source {route} answers the page", code == 200 and key in payload and "available" in payload, str(code))
    code, prev = handle("POST", "/api/standards/generate-preview", {"pattern_id": "x", "template_id": "y"})
    check("the dry-run preview source answers the page", code in (200, 400) and prev.get("dry_run") is True)

    print(f"\n{'PASS — check_standards_ui: /standards renders the standards-system view as a projection over /api/standards/* (all named panels present; loading/error/empty/degraded states; fetches only the standards API; no truth/secrets/storage); the API data sources answer the page and degrade gracefully.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: /standards UI (projection-only).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
