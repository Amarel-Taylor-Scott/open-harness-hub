#!/usr/bin/env python3
"""scripts.check_monolith_allowlist — proof: no governed-scope file exceeds its line budget unless it is
allowlisted with a reason + split target + deadline pass. Monolith drift becomes measured and gated.

CLI: python3 scripts/check_monolith_allowlist.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DEFAULT_FAIL = 500           # default fail budget for governed .py
_API_SERVER_FAIL = 750        # the admin/HTTP server budget
_API_SERVER = "scripts/baltor_admin_demo_server.py"


def _budget(rel: str) -> int:
    return _API_SERVER_FAIL if rel == _API_SERVER else _DEFAULT_FAIL


def _governed_files(globs: list[str]) -> list[Path]:
    out: list[Path] = []
    for g in globs:
        out += [p for p in _REPO.glob(g) if p.is_file() and p.suffix == ".py" and "__pycache__" not in p.parts]
    return sorted(set(out))


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    m = json.loads((_REPO / "architecture" / "monolith_allowlist.json").read_text())
    allow = {e["path"]: e for e in m["allowlist"]}

    over = []
    for p in _governed_files(m["governed_globs"]):
        rel = str(p.relative_to(_REPO))
        n = sum(1 for _ in p.open(encoding="utf-8", errors="ignore"))
        if n > _budget(rel):
            over.append((rel, n))
    unlisted = [f"{r}:{n}" for r, n in over if r not in allow]
    check("no governed file over budget OUTSIDE the allowlist", unlisted == [], str(unlisted))
    check("the known API monolith (admin server) is allowlisted", _API_SERVER in allow)
    check("every allowlist entry has reason + target_split + deadline_pass",
          all(all(k in e for k in ("reason", "target_split", "deadline_pass")) for e in m["allowlist"]))
    check("every allowlisted monolith still exists (no stale allowlist)",
          all((_REPO / p).exists() for p in allow), str([p for p in allow if not (_REPO / p).exists()]))
    check("allowlist is bounded (debt is visible, not unbounded)", len(allow) <= 5, str(len(allow)))

    print(f"\n{'PASS — check_monolith_allowlist: monolith growth is measured + gated; the one legacy over-budget file (admin server) is allowlisted with a split target + deadline.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: monolith allowlist + line budgets.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
