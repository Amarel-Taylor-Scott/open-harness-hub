#!/usr/bin/env python3
"""scripts.check_project_spine_folders — proof: the approved project spine exists and is well-formed.

Reads _repos/shared-backend-components/architecture/project_spine.json and asserts every required folder exists, the governed-scope paths
exist, and every layer declares purpose + allowed_project_imports + forbidden_imports. This is the folder
taxonomy made into a failing fitness function: a future module has an approved home to land in.

CLI: python3 _repos/shared-backend-components/scripts/check_project_spine_folders.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    spine = json.loads((_resource("architecture") / "project_spine.json").read_text())
    missing = [f for f in spine["required_folders"] if not (_resource(f)).is_dir()]
    check(f"all {len(spine['required_folders'])} required spine folders exist", missing == [], str(missing[:8]))
    check("governed_scope paths exist", all((_resource(p)).exists() for p in spine["governed_scope"]),
          str([p for p in spine["governed_scope"] if not (_resource(p)).exists()]))
    check("every layer declares purpose + allowed + forbidden imports",
          all(all(k in v for k in ("paths", "purpose", "allowed_project_imports", "forbidden_imports"))
              for v in spine["layers"].values()))
    check("_repos/baltor/backend/src/baltor package dirs carry __init__.py",
          all((_resource(d) / "__init__.py").exists() for d in spine["required_folders"] if d.startswith("_repos/baltor/backend/src/baltor")))
    check("the spine is layered (contracts/ports/adapters/runtime/processors present)",
          {"contracts", "ports", "adapters", "runtime", "processors"} <= set(spine["layers"]))

    print(f"\n{'PASS — check_project_spine_folders: the approved folder taxonomy exists, governed scope is present, and every layer is declared.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: project spine folders exist.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
