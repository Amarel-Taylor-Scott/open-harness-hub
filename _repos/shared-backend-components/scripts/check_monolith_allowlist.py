#!/usr/bin/env python3
"""scripts.check_monolith_allowlist — proof: no governed-scope file exceeds its line budget unless it is
allowlisted with a reason + split target + deadline pass. Monolith drift becomes measured and gated.

CLI: python3 _repos/shared-backend-components/scripts/check_monolith_allowlist.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
# scripts/* moved under _repos/shared-backend-components/ in the _repos/ migration. Glob + relative_to the
# scripts/-prefixed governed paths against THIS base so "scripts/runtime/*.py" matches real files and
# relative_to yields "scripts/…" (matching the allowlist keys). Non-scripts globs (e.g. _repos/baltor/**)
# still resolve against the repo root (_REPO).
_SCRIPTS_BASE = _resource("scripts").parent   # = _repos/shared-backend-components


def _base_for(rel: str) -> Path:
    """Base dir a governed glob/path resolves under: scripts/* under _SCRIPTS_BASE; everything else under _REPO."""
    return _SCRIPTS_BASE if rel.startswith("scripts/") else _REPO


def _rel(p: Path) -> str:
    """Rel path matching the allowlist keys: scripts files → 'scripts/…'; baltor files → '_repos/baltor/…'."""
    for base in (_SCRIPTS_BASE, _REPO):
        try:
            return str(p.relative_to(base))
        except ValueError:
            continue
    return str(p)


_DEFAULT_FAIL = 500           # default fail budget for governed .py
_API_SERVER_FAIL = 750        # the admin/HTTP server budget
_API_SERVER = "scripts/baltor_admin_demo_server.py"


def _budget(rel: str) -> int:
    return _API_SERVER_FAIL if rel == _API_SERVER else _DEFAULT_FAIL


def _governed_files(globs: list[str]) -> list[Path]:
    out: list[Path] = []
    for g in globs:
        out += [p for p in _base_for(g).glob(g) if p.is_file() and p.suffix == ".py" and "__pycache__" not in p.parts]
    return sorted(set(out))


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    m = json.loads((_resource("architecture") / "monolith_allowlist.json").read_text())
    allow = {e["path"]: e for e in m["allowlist"]}

    over = []
    for p in _governed_files(m["governed_globs"]):
        rel = _rel(p)
        n = sum(1 for _ in p.open(encoding="utf-8", errors="ignore"))
        if n > _budget(rel):
            over.append((rel, n))
    unlisted = [f"{r}:{n}" for r, n in over if r not in allow]
    check("no governed file over budget OUTSIDE the allowlist", unlisted == [], str(unlisted))
    check("the known API monolith (admin server) is allowlisted", _API_SERVER in allow)
    check("every allowlist entry has reason + target_split + deadline_pass + current_lines",
          all(all(k in e for k in ("reason", "target_split", "deadline_pass", "current_lines")) for e in m["allowlist"]))
    check("every allowlisted monolith still exists (no stale allowlist)",
          all((_base_for(p) / p).exists() for p in allow), str([p for p in allow if not (_base_for(p) / p).exists()]))
    check("allowlist is bounded (debt is visible, not unbounded)", len(allow) <= 5, str(len(allow)))

    # RATCHET: an allowlisted monolith may SHRINK but never GROW past its recorded current_lines — otherwise the
    # allowlist silently hides unbounded growth (the admin server had drifted 5445->6394 undetected). Counted via
    # the SAME line counter as the budget check so the baseline and the comparison can never disagree.
    grew = []
    for e in m["allowlist"]:
        p = _base_for(e["path"]) / e["path"]
        if p.exists() and "current_lines" in e:
            actual = sum(1 for _ in p.open(encoding="utf-8", errors="ignore"))
            if actual > int(e["current_lines"]):
                grew.append(f"{e['path']} grew {e['current_lines']}->{actual}")
    check("no allowlisted monolith grew past its recorded current_lines (ratchet: shrink ok, growth forbidden)",
          grew == [], str(grew))

    # DEADLINE: once the flywheel pass counter reaches an entry's deadline_pass, a STILL-over-budget monolith is no
    # longer waived — mirrors the pattern_waivers expiry rule, reading its single-source current_pass (no 2nd counter).
    pw = json.loads((_resource("architecture") / "pattern_waivers.json").read_text())
    current_pass = int(pw.get("current_pass", 0))
    past_deadline = []
    for e in m["allowlist"]:
        p = _base_for(e["path"]) / e["path"]
        deadline = int(str(e.get("deadline_pass", "")).lstrip("Cc") or 0)
        if p.exists() and deadline:
            actual = sum(1 for _ in p.open(encoding="utf-8", errors="ignore"))
            if actual > _budget(e["path"]) and current_pass >= deadline:
                past_deadline.append(f"{e['path']} past deadline C{deadline} (pass {current_pass}) still {actual}>budget")
    check("no allowlisted monolith is past its split deadline while still over budget (deadline is enforceable)",
          past_deadline == [], str(past_deadline))

    print(f"\n{'PASS — check_monolith_allowlist: monolith growth is measured + gated; allowlisted files ratchet (shrink ok, growth forbidden); the split deadline is enforceable against the flywheel pass counter.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
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
