#!/usr/bin/env python3
"""scripts.check_no_direct_external_imports — proof (C35): a cataloged provider package (an adapter's
import_module) may ONLY be imported inside an approved adapter path (src/baltor/adapters, the LLM gateways).
Domain/runtime/processor code depends on a capability port, never on a vendor SDK directly. Today nothing
imports a provider package, so this passes — and it stays a wall when the first adapter is implemented.

Complements check_no_direct_provider_bypass (which is LLM-SDK specific): this covers ALL cataloged providers
(parser/vector/graph/scrape/durable/observability/...).

CLI: python3 scripts/check_no_direct_external_imports.py --self-test
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

_GOVERNED = ["src/baltor", "scripts/runtime", "scripts/artifact_graph", "scripts/llm_gateway", "scripts/security", "scripts/pipeline_runtime"]


def _governed_py() -> list[Path]:
    out: list[Path] = []
    for d in _GOVERNED:
        p = _REPO / d
        if p.is_dir():
            out += [f for f in p.rglob("*.py") if "__pycache__" not in f.parts]
    return sorted(set(out))


def _top_level_imports(tree: ast.AST) -> set[str]:
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                mods.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                mods.add(node.module.split(".")[0])
    return mods


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = CapabilityRegistry()
    provider_mods = set(reg.import_modules())
    approved = [a.rstrip("/") for a in reg.approved_adapter_paths()]
    check("approved adapter paths are declared", len(approved) >= 1, str(approved))

    offenders: list[str] = []
    for f in _governed_py():
        rel = str(f.relative_to(_REPO))
        if any(rel == a or rel.startswith(a + "/") for a in approved):
            continue  # provider imports are legal inside an approved adapter path
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError as e:
            fails.append(f"unparseable {rel}: {e}"); continue
        for mod in _top_level_imports(tree):
            if mod in provider_mods:
                offenders.append(f"{rel} imports provider SDK {mod!r} outside an approved adapter path")
    check("no provider SDK imported outside an approved adapter path", offenders == [], str(offenders[:8]))

    print(f"\n{'PASS — check_no_direct_external_imports: provider SDKs may only be imported behind approved adapter paths; domain/runtime code depends on capability ports.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: provider SDKs only behind approved adapter paths.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
