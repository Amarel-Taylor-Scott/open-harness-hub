#!/usr/bin/env python3
"""scripts.check_architecture_adr_coverage — proof: the load-bearing architecture decisions (project spine,
runtime ownership, contract-first communication) have ADRs with the required sections + enforcement proofs.

CLI: python3 scripts/check_architecture_adr_coverage.py --self-test
"""
from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_ADR = _REPO / "docs" / "adr"
_REQUIRED = ("0001-project-spine-and-layering.md", "0002-runtime-ownership-and-no-duplicate-frameworks.md",
             "0003-contract-first-module-communication.md")
_SECTIONS = ("## Status", "## Context", "## Decision", "## Consequences", "## Enforcement proofs")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    for adr in _REQUIRED:
        p = _ADR / adr
        if not p.exists():
            check(f"ADR {adr} exists", False); continue
        text = p.read_text(encoding="utf-8")
        missing = [s for s in _SECTIONS if s not in text]
        check(f"ADR {adr} has all required sections", missing == [], str(missing))
        check(f"ADR {adr} names an enforcement proof", "check_" in text)

    check("the three load-bearing ADRs are present (spine, ownership, contract-first)",
          all((_ADR / a).exists() for a in _REQUIRED))

    print(f"\n{'PASS — check_architecture_adr_coverage: the spine / ownership / contract-first decisions are recorded as ADRs with status, context, decision, consequences, and enforcement proofs.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: ADR coverage.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
