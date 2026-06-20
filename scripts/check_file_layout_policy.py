#!/usr/bin/env python3
"""scripts.check_file_layout_policy — proof: no banned vague filenames (utils/helpers/common/temp/…) appear
in the governed scope outside the allowlist, no unapproved top-level folder exists, and the allowlist has no
stale entries. File-organization drift becomes a failing check.

CLI: python3 scripts/check_file_layout_policy.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
# local-only dirs that are gitignored and never part of the tracked tree (tooling caches +
# the dated rollback snapshot kept on disk under the lossless law — see archive/<date>/README)
_SKIP = {".venv", "__pycache__", ".git", "node_modules", "_reference", "archive"}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    pol = json.loads((_REPO / "architecture" / "file_layout_policy.json").read_text())
    banned = set(pol["banned_filenames"])
    allow = {e["path"] for e in pol["banned_filename_allowlist"]}

    hits = []
    for scope in pol["scan_scope"]:
        for p in (_REPO / scope).rglob("*.py"):
            if any(part in _SKIP for part in p.parts):
                continue
            rel = str(p.relative_to(_REPO))
            if p.name in banned and rel not in allow:
                hits.append(rel)
    check("no banned vague filenames in governed scope (outside allowlist)", hits == [], str(hits))
    check("banned-filename allowlist has no STALE entries (every allowlisted file exists)",
          all((_REPO / a).exists() for a in allow), str([a for a in allow if not (_REPO / a).exists()]))

    approved = set(pol["approved_top_level"])
    actual = {p.name for p in _REPO.iterdir() if p.is_dir() and not p.name.startswith(".") and p.name not in _SKIP}
    unapproved = sorted(actual - approved)
    check("no UNAPPROVED top-level folder exists", unapproved == [], str(unapproved))
    check("scripts policy + reusable-code home declared",
          "scripts/" in pol["scripts_policy"] and pol["reusable_code_home"] == "src/baltor")

    print(f"\n{'PASS — check_file_layout_policy: no banned filenames or unapproved top-level folders; the allowlist is current. New file-organization drift fails.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: file layout policy.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
