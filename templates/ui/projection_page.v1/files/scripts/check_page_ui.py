#!/usr/bin/env python3
"""scripts.check_{{page}}_ui — proof of standard.ui_projection.v1 for {{title}}.

GENERATED STUB (standard.proof_script.v1). Asserts the page exists, references only the projection endpoint
{{api_endpoint}}, carries the projection-only marker, and embeds NO secret literal. Deterministic + offline +
--self-test + PASS/FAIL + exit 0/1.

CLI: python3 scripts/check_{{page}}_ui.py --self-test
"""
from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_PAGE = _REPO / "web" / "baltor" / "{{page}}.html"
_SECRET_MARKERS = ("OH_SHOWCASE_TOKEN", "sk-", "api_key", "Authorization")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    exists = _PAGE.exists()
    check("page exists", exists, str(_PAGE))
    if exists:
        html = _PAGE.read_text()
        check("references the projection endpoint", "{{api_endpoint}}" in html)
        check("carries the projection-only marker", "PROJECTION ONLY" in html.upper())
        check("no secret literal embedded", not any(m in html for m in _SECRET_MARKERS))

    print(f"{'PASS' if not fails else 'FAIL'} check_{{page}}_ui ({len(fails)} failing)")
    return 0 if not fails else 1


def _main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Proof: {{page}} projection UI page.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
