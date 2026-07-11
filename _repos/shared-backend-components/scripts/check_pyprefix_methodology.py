#!/usr/bin/env python3
"""Validate the pyprefix migration methodology contract.

This is not the full proof gate. It checks that the machine-readable methodology rules exist, that
repo-wide pyprefix scans are scoped to owned source, and that every path marked `migrated` is still
100% conformant. The runtime oracle remains _repos/shared-backend-components/scripts/run_proofs.py.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from scripts import pyprefix
REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
RULES = _resource("architecture") / "pyprefix_methodology_rules.json"
MANIFEST = _resource("architecture") / "pyprefix_migration.json"

REQUIRED_RULES = {
    "owned-source-only",
    "package-sized-migration",
    "proof-gate-is-oracle",
    "migrated-means-zero-violations",
    "dynamic-refs-are-unresolved",
    "contract-renames-are-coordinated",
    "external-entrypoints-use-shims",
    "names-are-meaningful-not-hashes",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _failures() -> list[str]:
    failures: list[str] = []
    rules = _load_json(RULES)
    ids = {r.get("id") for r in rules.get("rules", [])}
    missing = REQUIRED_RULES - ids
    if missing:
        failures.append(f"missing methodology rule id(s): {sorted(missing)}")

    files = pyprefix._py_files(REPO)  # owned-source scope by design
    bad_parts = {".venv", "_reference", "archive", "dist", "site", "data", ".agent"}
    leaked = [str(f) for f in files if any(part in bad_parts for part in f.parts)]
    if leaked:
        failures.append(f"owned-source scan leaked excluded paths: {leaked[:5]}")

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / ".venv").mkdir()
        (root / ".venv" / "third_party.py").write_text("def nope():\n    pass\n", encoding="utf-8")
        (root / "src").mkdir()
        (root / "src" / "owned.py").write_text("def ok():\n    return 1\n", encoding="utf-8")
        got = {p.name for p in pyprefix._py_files(root)}
        if "third_party.py" in got or "owned.py" not in got:
            failures.append("path exclusion failed for explicit temp root")

    manifest = _load_json(MANIFEST)
    for rel in manifest.get("migrated", []):
        path = _resource(rel)
        violations = pyprefix.check_path(path)
        if violations:
            failures.append(f"migrated path drifted: {rel} has {len(violations)} violation(s)")

    return failures


def _self_test() -> int:
    failures = _failures()
    if failures:
        for failure in failures:
            print(f"FAIL - {failure}")
        return 1
    print("PASS - pyprefix methodology rules: required ids, owned-source scope, exclusions, migrated conformance")
    return 0


def main() -> int:
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(main())
