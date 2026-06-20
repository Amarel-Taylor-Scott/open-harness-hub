#!/usr/bin/env python3
"""scripts.check_no_uncataloged_github_repos — proof (C35): inside the GOVERNED runtime scope (src/baltor +
scripts/{runtime,artifact_graph,llm_gateway,security}), every imported 3rd-party package must have an adapter
card in the External Capability Catalog. The governed runtime is stdlib-only today, so this passes today — but
the moment someone imports e.g. `docling` without a catalog card, the build fails. (This is NOT a whole-repo
grep for github.com URLs; it is a real import scan via the AST, scoped to the governed runtime.)

CLI: python3 scripts/check_no_uncataloged_github_repos.py --self-test
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from src.baltor.runtime.registry.capability_registry import CapabilityRegistry  # noqa: E402

#: the governed runtime scope (not the whole repo, not legacy OHH code).
_GOVERNED = ["src/baltor", "scripts/runtime", "scripts/artifact_graph", "scripts/llm_gateway", "scripts/security"]


def _governed_py() -> list[Path]:
    out: list[Path] = []
    for d in _GOVERNED:
        p = _REPO / d
        if p.is_dir():
            out += [f for f in p.rglob("*.py") if "__pycache__" not in f.parts]
    return sorted(set(out))


def _first_party() -> set[str]:
    names = {"src", "scripts", "baltor"}
    for p in _REPO.iterdir():
        if p.is_dir() and not p.name.startswith("."):
            names.add(p.name)
        elif p.suffix == ".py":
            names.add(p.stem)
    return names


def _top_level_imports(tree: ast.AST) -> set[str]:
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                mods.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:  # absolute import only; relative is internal
                mods.add(node.module.split(".")[0])
    return mods


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = CapabilityRegistry()
    cataloged = set(reg.import_modules())
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    internal = _first_party()
    allowed = stdlib | internal | cataloged

    offenders: list[str] = []
    files = _governed_py()
    check("found governed runtime files to scan", len(files) >= 1, str(len(files)))
    for f in files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError as e:
            fails.append(f"unparseable {f.relative_to(_REPO)}: {e}"); continue
        for mod in _top_level_imports(tree):
            if mod not in allowed:
                offenders.append(f"{f.relative_to(_REPO)} imports uncataloged 3rd-party {mod!r}")
    check("no uncataloged 3rd-party import in the governed runtime scope", offenders == [], str(offenders[:8]))
    check("the catalog provides a non-empty import-module allowlist", len(cataloged) >= 1, str(len(cataloged)))

    print(f"\n{'PASS — check_no_uncataloged_github_repos: every 3rd-party import in the governed runtime is cataloged (stdlib-only today). The first real dependency cannot land without a card.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: no uncataloged 3rd-party imports in governed scope.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
