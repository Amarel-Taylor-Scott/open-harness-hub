#!/usr/bin/env python3
"""scripts.check_file_layout_policy — proof: no banned vague filenames (utils/helpers/common/temp/…) appear
in the governed scope outside the allowlist, no unapproved top-level folder exists, and the allowlist has no
stale entries. File-organization drift becomes a failing check.

CLI: python3 _repos/shared-backend-components/scripts/check_file_layout_policy.py --self-test
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
# local-only dirs that are gitignored and never part of the tracked tree (tooling caches +
# the dated rollback snapshot kept on disk under the lossless law — see archive/<date>/README).
# NOTE: this is a minimal seed; any OTHER gitignored top-level dir is skipped dynamically via
# _gitignored() below, so untracked local cruft never counts as a layout violation (no drift-prone
# hardcoded list — a new gitignored dir is auto-excluded).
_SKIP = {".venv", "__pycache__", ".git", "node_modules", "_reference", "archive"}


def _gitignored(names: list[str]) -> set[str]:
    """Of the given top-level dir names, the subset git ignores (local-only, not tracked repo layout).
    One `git check-ignore` call; empty set if git is unavailable so the check still runs offline."""
    if not names:
        return set()
    try:
        r = subprocess.run(["git", "check-ignore", *names], cwd=_REPO, capture_output=True, text=True)
        return {ln.strip().rstrip("/").split("/")[0] for ln in r.stdout.splitlines() if ln.strip()}
    except Exception:  # noqa: BLE001 — offline / no git: fall back to the static _SKIP only
        return set()


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    pol = json.loads((_resource("architecture") / "file_layout_policy.json").read_text())
    banned = set(pol["banned_filenames"])
    allow = {e["path"] for e in pol["banned_filename_allowlist"]}

    hits = []
    for scope in pol["scan_scope"]:
        for p in (_resource(scope)).rglob("*.py"):
            if any(part in _SKIP for part in p.parts):
                continue
            rel = str(p.relative_to(_REPO))
            if p.name in banned and rel not in allow:
                hits.append(rel)
    check("no banned vague filenames in governed scope (outside allowlist)", hits == [], str(hits))
    check("banned-filename allowlist has no STALE entries (every allowlisted file exists)",
          all((_resource(a)).exists() for a in allow), str([a for a in allow if not (_resource(a)).exists()]))

    approved = set(pol["approved_top_level"])
    _dirs = [p.name for p in _REPO.iterdir() if p.is_dir() and not p.name.startswith(".") and p.name not in _SKIP]
    actual = set(_dirs) - _gitignored(_dirs)   # untracked gitignored cruft is not a layout violation
    unapproved = sorted(actual - approved)
    check("no UNAPPROVED top-level folder exists", unapproved == [], str(unapproved))
    check("scripts policy + reusable-code home declared",
          "scripts/" in pol["scripts_policy"] and pol["reusable_code_home"] == "_repos/baltor/backend/src/baltor")

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
