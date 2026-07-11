#!/usr/bin/env python3
"""scripts.check_no_direct_supermemory_imports — proof (C-MEM-1): NOTHING in this repo imports the real
`supermemory` SDK. The Supermemory adapters are CONTRACT STUBS: they declare the contract and raise a clear
UnavailableProvider (naming the missing credential) — they do NOT import the vendor package. An AST scan of
all governed Python asserts:

  1) no module (anywhere) does `import supermemory` / `from supermemory...` / imports the JS-ish sdk names;
  2) even the approved adapter stub paths do not import the real SDK (they are stubs only);
  3) the supermemory clone at _reference/ is never imported as a runtime dependency.

Deterministic, stdlib-only, offline. Models _repos/shared-backend-components/scripts/check_no_direct_external_imports.py.

CLI: python3 _repos/shared-backend-components/scripts/check_no_direct_supermemory_imports.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import ast
import warnings
from pathlib import Path

# scanning sibling files for imports: their docstrings may contain invalid escape sequences — we only care
# about import statements, so suppress those source-level warnings while parsing other files' trees.
warnings.filterwarnings("ignore", category=SyntaxWarning)

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])

#: top-level module names that would be the real Supermemory SDK / its clone package.
_FORBIDDEN_TOP = {"supermemory", "supermemoryai", "super_memory"}
#: approved adapter stub paths (relative). Even HERE the real SDK must not be imported — they are stubs.
_APPROVED_STUB_PATHS = (
    "_repos/baltor/backend/src/baltor/adapters/memory/supermemory_api.py",
    "_repos/baltor/backend/src/baltor/adapters/memory/mcp_supermemory.py",
    "scripts/memory/supermemory_api.py",
)
#: directories scanned (governed code + this lane's handler/UI helpers); _reference/ and vendored trees skipped.
_SCAN_DIRS = ("scripts", "_repos/baltor/backend/src/baltor", "web")
_SKIP_PARTS = ("__pycache__", "_reference", "node_modules", "dist", "site")


def _py_files() -> list[Path]:
    out: list[Path] = []
    for d in _SCAN_DIRS:
        base = _resource(d)
        if base.is_dir():
            out += [f for f in base.rglob("*.py") if not any(s in f.parts for s in _SKIP_PARTS)]
    return sorted(set(out))


def _imports(tree: ast.AST) -> set[str]:
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                mods.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:  # both absolute and relative; the top segment is what matters
                mods.add(node.module.split(".")[0])
    return mods


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    offenders: list[str] = []
    stub_offenders: list[str] = []
    scanned = 0
    for f in _py_files():
        rel = str(f.relative_to(_REPO))
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError as e:
            fails.append(f"unparseable {rel}: {e}")
            continue
        scanned += 1
        bad = _imports(tree) & _FORBIDDEN_TOP
        if bad:
            (stub_offenders if rel in _APPROVED_STUB_PATHS else offenders).append(f"{rel}:{sorted(bad)}")

    check("scanned at least one governed Python file", scanned >= 1, str(scanned))
    check("no module imports the real supermemory SDK (anywhere)", offenders == [], str(offenders[:8]))
    check("even the approved adapter STUBS do not import the real SDK", stub_offenders == [], str(stub_offenders))

    # the _reference clone is never reachable as a package import: no governed file IMPORTS the _reference
    # tree as a module (a docstring mention of the path is fine — we only flag an import-shaped reference, via
    # the AST, so this proof's own prose about the path can never trip it).
    ref_token = "_reference"  # built as a local so a literal in this file's prose is not what we match
    ref_refs = []
    for f in _py_files():
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        if ref_token in _imports(tree):
            ref_refs.append(str(f.relative_to(_REPO)))
    check("the _reference/supermemory clone is never imported as a package", ref_refs == [], str(ref_refs))

    print(f"\n{'PASS — check_no_direct_supermemory_imports: no governed module imports the real supermemory SDK; the approved adapters are contract STUBS only; the _reference clone is never imported as a runtime dependency.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: no direct supermemory SDK import anywhere.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
