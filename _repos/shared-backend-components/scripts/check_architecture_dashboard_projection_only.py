#!/usr/bin/env python3
"""scripts.check_architecture_dashboard_projection_only — proof: _repos/baltor/frontend pages are projections only —
they never write durable truth and never embed private memory/intel. Dashboard-truth drift fails.

CLI: python3 _repos/shared-backend-components/scripts/check_architecture_dashboard_projection_only.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
_WEB = _resource("web/baltor")
#: writing/owning durable truth from a page is forbidden on EVERY page.
_WRITE_FORBIDDEN = ("durable.db", "INSERT INTO", "UPDATE ", "DELETE FROM", "import sqlite3", "sqlite3.connect")
#: embedding private memory/intel is forbidden on PUBLIC pages; the internal /dev tool legitimately renders
#: dev-receipt labels (it is read-only and its purpose is to surface build/dev state).
#: NOTE: the private-memory marker is ".claude/" (the agent's private memory/transcript root), NOT a bare
#: "/memory/" — the latter collided with the legitimate MemoryProvider product API namespace "/api/memory/".
_PRIVATE_FORBIDDEN = (".agent/", "MEMORY.md", "baltor-goal-loop", ".claude/")
_INTERNAL_DEV_PAGES = {"dev-dashboard.html"}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    pages = sorted(_WEB.rglob("*.html"))
    check("_repos/baltor/frontend has pages to check", len(pages) >= 4, str(len(pages)))

    write_offenders, private_offenders = [], []
    for p in pages:
        text = p.read_text(encoding="utf-8", errors="ignore")
        for bad in _WRITE_FORBIDDEN:
            if bad in text:
                write_offenders.append(f"{p.name}:{bad}")
        if p.name not in _INTERNAL_DEV_PAGES:
            for bad in _PRIVATE_FORBIDDEN:
                if bad in text:
                    private_offenders.append(f"{p.name}:{bad}")
    check("NO web page writes durable truth (projection-only everywhere)", write_offenders == [], str(write_offenders))
    check("no PUBLIC page embeds private memory/intel (internal /dev tool exempt)", private_offenders == [], str(private_offenders))

    # positive signal: pages read via the API (fetch), i.e. they consume projections
    consumes_api = sum(1 for p in pages if "/api/" in p.read_text(encoding="utf-8", errors="ignore"))
    check("pages consume API projections (fetch /api/…), not their own store", consumes_api >= 3, str(consumes_api))

    print(f"\n{'PASS — check_architecture_dashboard_projection_only: web pages are projection-only (no durable writes, no private memory) and consume API projections.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: dashboard is projection-only.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
